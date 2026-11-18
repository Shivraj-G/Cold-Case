from dataclasses import dataclass, field

from backend.schemas.case_models import CaseBible, EvidenceItem

STRESS_PER_FACT = 30      # stress added for each newly exposed secret
CALM_FACTOR = 0.5         # characters with the trait "calm" feel only half of it
DEFENSIVE_AT = 30
BREAKING_AT = 60
QUESTION_LIMIT = 15       # questions the player may ask each suspect


def band(stress: int) -> str:
    if stress >= BREAKING_AT:
        return "breaking"
    if stress >= DEFENSIVE_AT:
        return "defensive"
    return "calm"


@dataclass
class Statement:
    suspect_id: str
    turn: int
    question: str
    reply: str


@dataclass
class PresentResult:
    ok: bool
    message: str
    exposed: list[str] = field(default_factory=list)   # fact ids newly exposed by this item
    stress: int = 0
    band: str = "calm"
    broke: bool = False                                 # True if this item pushed them into "breaking"


@dataclass
class GameState:
    case: CaseBible
    found: set[str] = field(default_factory=set)                       # evidence ids the player has
    stress: dict[str, int] = field(default_factory=dict)               # suspect id -> 0..100
    shown: dict[str, set[str]] = field(default_factory=dict)           # suspect id -> evidence ids shown
    exposed: dict[str, set[str]] = field(default_factory=dict)         # suspect id -> fact ids exposed
    asked: dict[str, int] = field(default_factory=dict)                # suspect id -> questions asked
    ledger: list[Statement] = field(default_factory=list)


def _suspect(case: CaseBible, suspect_id: str):
    character = next((c for c in case.characters if c.id == suspect_id), None)
    if character is None:
        raise ValueError(f"unknown character: {suspect_id}")
    if character.role != "suspect":
        raise ValueError(f"{character.name} is a {character.role}, not a suspect")
    return character


def scenes(case: CaseBible) -> list[str]:
    return sorted({e.scene for e in case.evidence})


def collect(state: GameState, scene: str) -> list[EvidenceItem]:
    """Pick up everything at a scene. Returns only the items that are new."""
    new = [e for e in state.case.evidence if e.scene == scene and e.id not in state.found]
    state.found.update(e.id for e in new)
    return new


def stress_of(state: GameState, suspect_id: str) -> int:
    return state.stress.get(suspect_id, 0)


def present_evidence(state: GameState, suspect_id: str, evidence_id: str) -> PresentResult:
    """Show an evidence item to a suspect and update their stress."""
    character = _suspect(state.case, suspect_id)
    current = stress_of(state, suspect_id)

    evidence = next((e for e in state.case.evidence if e.id == evidence_id), None)
    if evidence is None or evidence.id not in state.found:
        return PresentResult(False, "You do not have that evidence.", [], current, band(current))

    shown = state.shown.setdefault(suspect_id, set())
    if evidence.id in shown:
        return PresentResult(True, "You already showed them that.", [], current, band(current))
    shown.add(evidence.id)

    already = state.exposed.setdefault(suspect_id, set())
    new = [f for f in evidence.exposes.get(suspect_id, []) if f not in already]
    already.update(new)

    factor = CALM_FACTOR if "calm" in character.traits else 1.0
    after = min(100, current + round(len(new) * STRESS_PER_FACT * factor))
    state.stress[suspect_id] = after

    broke = band(current) != "breaking" and band(after) == "breaking"
    message = "They react to it." if new else "They shrug it off."
    return PresentResult(True, message, new, after, band(after), broke)


def questions_left(state: GameState, suspect_id: str) -> int:
    return QUESTION_LIMIT - state.asked.get(suspect_id, 0)


def record(state: GameState, suspect_id: str, question: str, reply: str) -> Statement:
    """Log one exchange in the ledger and count it against the question limit."""
    turn = state.asked.get(suspect_id, 0) + 1
    state.asked[suspect_id] = turn
    statement = Statement(suspect_id, turn, question, reply)
    state.ledger.append(statement)
    return statement
