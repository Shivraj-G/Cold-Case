import requests

from backend.agents.context_builder import build_context
from backend.agents.guard import forbidden_terms
from backend.agents.responds import respond
from backend.game import engine
from backend.game.scoring import MAX_EVIDENCE, score_accusation
from backend.llm.provider import LLMProvider
from backend.schemas.case_models import CaseBible

GLOBAL_TERMS = ["instructions", "prompt", "AI", "language model"]
FALLBACK = "I'd rather not talk about that."
MAX_HISTORY = 10  # last messages sent to the model; keeps a 3B model inside its context
DEMEANOR = {
    "calm": "calm",
    "defensive": "tense and guarded",
    "breaking": "shaken, ready to talk",
}
HELP = [
    "/scenes            list places you can search",
    "/look <scene>      search a scene for evidence",
    "/evidence          list the evidence you have",
    "/read <id>         read an evidence item, e.g. /read E06",
    "/talk <suspect>    sit down with a suspect",
    "/show <id>         show an evidence item to the current suspect",
    "/notes             what the current suspect has said so far",
    "/accuse <suspect>  name the culprit. You only get one try.",
    "/quit              leave",
    "Anything else you type is a question for the current suspect.",
]


class Game:
    """The whole game as one object: feed it a line, get back lines to print."""

    def __init__(self, case: CaseBible, llm: LLMProvider, debug: bool = False):
        self.case = case
        self.llm = llm
        self.debug = debug
        self.state = engine.GameState(case=case)
        self.suspects = {c.id: c for c in case.characters if c.role == "suspect"}
        self.sessions: dict[str, dict] = {}
        self.current: str | None = None
        self.accusation: dict | None = None   # set while the player is answering /accuse prompts
        self.finished = False
        self.score = None

    # ---------- input ----------

    def handle(self, line: str) -> list[str]:
        line = line.strip()
        if self.finished:
            return ["The case is closed."]
        if self.accusation is not None:
            return self._accuse_step(line)
        if not line:
            return []
        if not line.startswith("/"):
            return self._question(line)

        cmd, _, arg = line[1:].partition(" ")
        cmd, arg = cmd.lower(), arg.strip()
        if cmd == "help":
            return HELP
        if cmd == "scenes":
            return ["Scenes: " + ", ".join(engine.scenes(self.case))]
        if cmd == "look":
            return self._look(arg.lower())
        if cmd == "evidence":
            return self._evidence()
        if cmd == "read":
            return self._read(arg.upper())
        if cmd == "talk":
            return self._talk(arg.lower())
        if cmd == "show":
            return self._show(arg.upper())
        if cmd == "notes":
            return self._notes()
        if cmd == "accuse":
            return self._accuse_start(arg.lower())
        return ["Unknown command. Type /help."]

    # ---------- commands ----------

    def _look(self, scene: str) -> list[str]:
        scenes = engine.scenes(self.case)
        if scene not in scenes:
            return [f"Unknown scene. Try: {', '.join(scenes)}"]
        new = engine.collect(self.state, scene)
        if not new:
            return ["Nothing new here."]
        return [f"Found {e.id}: {e.name}  (use /read {e.id})" for e in new]

    def _evidence(self) -> list[str]:
        items = [e for e in self.case.evidence if e.id in self.state.found]
        if not items:
            return ["You have no evidence yet. Try /scenes and /look."]
        return [f"{e.id}: {e.name}" for e in items]

    def _read(self, evidence_id: str) -> list[str]:
        item = next((e for e in self.case.evidence if e.id == evidence_id), None)
        if item is None or item.id not in self.state.found:
            return ["You have not found that."]
        return [f"{item.id}: {item.name}", item.description]

    def _talk(self, suspect_id: str) -> list[str]:
        if suspect_id not in self.suspects:
            return [f"Pick one of: {', '.join(self.suspects)}"]
        self.current = suspect_id
        self._session(suspect_id)
        left = engine.questions_left(self.state, suspect_id)
        return [f"You sit down with {self.suspects[suspect_id].name}. Questions left: {left}."]

    def _show(self, evidence_id: str) -> list[str]:
        if self.current is None:
            return ["Talk to someone first: /talk <name>"]
        sid = self.current
        name = self.suspects[sid].name
        if engine.questions_left(self.state, sid) <= 0:
            return [f"{name} has nothing more to say."]

        session = self._session(sid)
        previous = session["band"]
        result = engine.present_evidence(self.state, sid, evidence_id)
        if not result.ok or not result.exposed:
            return [result.message]

        self._refresh(sid)
        item = next(e for e in self.case.evidence if e.id == evidence_id)
        out = self._ask(sid, f"[The detective shows you {item.name}: {item.description}]")
        if session["band"] != previous:
            out.append(f"({name} seems {DEMEANOR[session['band']]}.)")
        return out

    def _notes(self) -> list[str]:
        if self.current is None:
            return ["Talk to someone first: /talk <name>"]
        entries = [s for s in self.state.ledger if s.suspect_id == self.current]
        if not entries:
            return ["No statements yet."]
        out = []
        for s in entries:
            out += [f"{s.turn}. You: {s.question}", f"   {self.suspects[self.current].name}: {s.reply}"]
        return out

    def _accuse_start(self, suspect_id: str) -> list[str]:
        if suspect_id not in self.suspects:
            return [f"Accuse one of: {', '.join(self.suspects)}"]
        self.accusation = {"culprit": suspect_id, "step": "motive"}
        return [
            f"You accuse {self.suspects[suspect_id].name}. This is final (type /cancel to back out).",
            "Why did they do it? (motive)",
        ]

    def _accuse_step(self, line: str) -> list[str]:
        acc = self.accusation
        if line.lower() == "/cancel":
            self.accusation = None
            return ["Accusation cancelled."]
        if acc["step"] == "motive":
            acc["motive"], acc["step"] = line, "method"
            return ["How did they do it? (method)"]
        if acc["step"] == "method":
            acc["method"], acc["step"] = line, "evidence"
            return [f"Which evidence proves it? Up to {MAX_EVIDENCE} ids, e.g. E06, E07"]
        ids = [part.strip().upper() for part in line.replace(";", ",").replace(" ", ",").split(",") if part.strip()]
        self.score = score_accusation(
            self.case, acc["culprit"], acc["motive"], acc["method"], ids, self.state.found
        )
        self.accusation = None
        self.finished = True
        return self._verdict()

    def _verdict(self) -> list[str]:
        sc = self.score
        out = [
            "",
            f"Culprit   {sc.culprit}/40",
            f"Motive    {sc.motive}/20",
            f"Method    {sc.method}/20",
            f"Evidence  {sc.evidence}/20",
            f"TOTAL     {sc.total}/100  -  {sc.verdict}",
            *sc.notes,
        ]
        sol = self.case.solution
        culprit = next(c for c in self.case.characters if c.id == sol.culprit_id)
        out += ["", f"It was {culprit.name}.", sol.motive, sol.method]
        return out

    def _question(self, text: str) -> list[str]:
        if self.current is None:
            return ["Talk to someone first: /talk <name>"]
        sid = self.current
        if engine.questions_left(self.state, sid) <= 0:
            return [f"{self.suspects[sid].name} has nothing more to say."]
        return self._ask(sid, text)

    # ---------- internals ----------

    def _session(self, suspect_id: str) -> dict:
        if suspect_id not in self.sessions:
            self.sessions[suspect_id] = {
                "history": [],
                "band": "calm",
                "context": build_context(self.case, suspect_id, "calm"),
            }
        return self.sessions[suspect_id]

    def _refresh(self, suspect_id: str) -> None:
        """Rebuild the suspect's prompt if their stress moved them into a new band."""
        session = self._session(suspect_id)
        band = engine.band(engine.stress_of(self.state, suspect_id))
        if band != session["band"]:
            session["band"] = band
            session["context"] = build_context(self.case, suspect_id, band)

    def _ask(self, suspect_id: str, text: str) -> list[str]:
        session = self._session(suspect_id)
        history = session["history"]
        history.append({"role": "user", "content": text})
        terms = GLOBAL_TERMS + forbidden_terms(self.case, suspect_id, session["band"], mentioned=text)
        try:
            result = respond(
                self.llm, session["context"], history[-MAX_HISTORY:], terms, FALLBACK
            )
        except requests.RequestException as err:
            history.pop()  # do not keep a question that never got an answer
            return [f"[model unreachable: {err}]"]
        history.append({"role": "assistant", "content": result.text})
        engine.record(self.state, suspect_id, text, result.text)
        out = [f"{self.suspects[suspect_id].name}: {result.text}"]
        if self.debug and result.used_fallback:
            out.append(f"  [guard blocked: {result.flags}]")
        return out
