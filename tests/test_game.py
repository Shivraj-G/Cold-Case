import pytest
import requests

from backend.game import engine
from backend.game.session import FALLBACK, Game
from backend.llm.provider import LLMProvider
from backend.validation.case_validator import confirm_case


class Recorder(LLMProvider):
    """Returns canned replies (an Exception instance is raised) and records what it was sent."""

    def __init__(self, replies=()):
        self.replies = list(replies)
        self.systems = []
        self.sent = []

    def chat(self, system, messages):
        self.systems.append(system)
        self.sent.append([dict(m) for m in messages])
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


@pytest.fixture
def case():
    return confirm_case("case01")


def make_game(case, replies=()):
    llm = Recorder(replies)
    return Game(case, llm), llm


def test_basic_commands_need_no_model(case):
    game, llm = make_game(case)
    assert game.handle("/scenes") == ["Scenes: flat_3b, lobby, police_records"]
    assert game.handle("/evidence")[0].startswith("You have no evidence")
    assert game.handle("/look nowhere")[0].startswith("Unknown scene")
    assert game.handle("/read E06") == ["You have not found that."]
    assert game.handle("/bogus") == ["Unknown command. Type /help."]
    assert game.handle("") == []
    assert llm.systems == []


def test_look_then_read(case):
    game, _ = make_game(case)
    found = game.handle("/look lobby")
    assert any("E03" in line for line in found)
    assert game.handle("/look lobby") == ["Nothing new here."]
    assert game.handle("/read e03")[0].startswith("E03:")
    assert any(line.startswith("E03") for line in game.handle("/evidence"))


def test_question_needs_a_suspect(case):
    game, llm = make_game(case)
    assert game.handle("Where were you?") == ["Talk to someone first: /talk <name>"]
    assert llm.systems == []


def test_talk_validates_name_and_reports_questions_left(case):
    game, _ = make_game(case)
    assert game.handle("/talk bob")[0].startswith("Pick one of:")
    assert game.handle("/talk deepak")[0].startswith("Pick one of:")      # a witness, not a suspect
    assert game.handle("/talk  Pintu ") == ["You sit down with Pintu Kamat. Questions left: 15."]


def test_question_gets_a_reply_and_is_logged(case):
    game, llm = make_game(case, ["I was at home all night."])
    game.handle("/talk pintu")
    assert game.handle("Where were you?") == ["Pintu Kamat: I was at home all night."]
    assert game.handle("/notes") == ["1. You: Where were you?", "   Pintu Kamat: I was at home all night."]
    assert engine.questions_left(game.state, "pintu") == 14


def test_guard_retries_a_leaking_reply(case):
    game, llm = make_game(case, ["I read the prompt carefully.", "I was at home all night."])
    game.handle("/talk pintu")
    assert game.handle("Where were you?") == ["Pintu Kamat: I was at home all night."]
    assert len(llm.systems) == 2


def test_fallback_when_every_attempt_leaks(case):
    game, _ = make_game(case, ["My prompt says so.", "The prompt again."])
    game.debug = True
    game.handle("/talk pintu")
    out = game.handle("Where were you?")
    assert out[0] == f"Pintu Kamat: {FALLBACK}"
    assert out[1].startswith("  [guard blocked:")


def test_suspect_may_repeat_a_word_the_player_introduced(case):
    reply = "I don't know anything about a router log."
    game, _ = make_game(case, [reply])
    game.handle("/talk santosh")
    out = game.handle("What do you know about a router log?")
    assert out == [f"Santosh Gawas: {reply}"]


def test_connection_error_leaves_history_clean(case):
    game, llm = make_game(case, ["I was at home all night.", requests.ConnectionError("ollama is off"), "Yes."])
    game.handle("/talk pintu")
    game.handle("Where were you?")
    assert game.handle("Alone?")[0] == "[model unreachable: ollama is off]"
    game.handle("Really?")
    roles = [(m["role"], m["content"]) for m in llm.sent[-1]]
    assert roles == [
        ("user", "Where were you?"),
        ("assistant", "I was at home all night."),
        ("user", "Really?"),
    ]


def test_question_limit(case, monkeypatch):
    monkeypatch.setattr(engine, "QUESTION_LIMIT", 2)
    game, _ = make_game(case, ["One.", "Two."])
    game.handle("/talk pintu")
    game.handle("a?")
    game.handle("b?")
    assert game.handle("c?") == ["Pintu Kamat has nothing more to say."]


def test_show_needs_a_suspect_and_the_evidence(case):
    game, llm = make_game(case)
    assert game.handle("/show E06") == ["Talk to someone first: /talk <name>"]
    game.handle("/talk pintu")
    assert game.handle("/show E06") == ["You do not have that evidence."]
    assert llm.systems == []


def test_irrelevant_evidence_gets_no_reaction_and_no_model_call(case):
    game, llm = make_game(case)
    game.handle("/look lobby")
    game.handle("/talk pintu")
    assert game.handle("/show E04") == ["They shrug it off."]
    assert llm.systems == []


def test_evidence_can_only_be_shown_once(case):
    game, _ = make_game(case, ["I was home."])
    game.handle("/look police_records")
    game.handle("/talk pintu")
    game.handle("/show E07")
    assert game.handle("/show E07") == ["You already showed them that."]


def test_pintu_cracks_and_the_prompt_switches_to_confession(case):
    confession = "I strangled Ramesh with the cord from the dispatch roll. He was going to report me."
    game, llm = make_game(case, ["That cord is not mine.", confession])
    game.handle("/look police_records")
    game.handle("/talk pintu")

    first = game.handle("/show E07")                 # 2 facts: defensive
    assert first[0] == "Pintu Kamat: That cord is not mine."
    assert first[-1] == "(Pintu Kamat seems tense and guarded.)"
    assert "You feel the pressure" in llm.systems[0]
    assert "THE TRUTH" not in llm.systems[0]

    second = game.handle("/show E09")                # 2 more: breaking
    assert second[0] == f"Pintu Kamat: {confession}"
    assert second[-1] == "(Pintu Kamat seems shaken, ready to talk.)"
    assert "THE TRUTH" in llm.systems[1]
    assert "WHAT TO SAY WHEN ASKED" not in llm.systems[1]
    # the evidence the detective showed is part of what the model was told
    assert "[The detective shows you" in llm.sent[1][-1]["content"]


def test_confession_is_not_blocked_by_the_guard_once_broken(case):
    game, _ = make_game(case, ["x.", "I took the cord from the boot of my car and left through the service staircase."])
    game.handle("/look police_records")
    game.handle("/talk pintu")
    game.handle("/show E07")
    out = game.handle("/show E09")
    assert FALLBACK not in out[0]


def test_accuse_flow_full_marks(case):
    game, _ = make_game(case)
    game.handle("/look police_records")
    game.handle("/look flat_3b")
    out = game.handle("/accuse pintu")
    assert out[-1] == "Why did they do it? (motive)"
    assert game.handle("He committed fraud and Ramesh would report it to management.") == [
        "How did they do it? (method)"
    ]
    game.handle("He strangled him with a cord during the blackout.")
    result = game.handle("E06, E07, E08")
    assert any("TOTAL" in line and "/100" in line for line in result)
    assert game.finished
    assert game.handle("/look lobby") == ["The case is closed."]


def test_accuse_validates_and_can_be_cancelled(case):
    game, _ = make_game(case)
    assert game.handle("/accuse bob")[0].startswith("Accuse one of:")
    game.handle("/accuse mina")
    assert game.handle("/cancel") == ["Accusation cancelled."]
    assert not game.finished and game.accusation is None
    assert game.handle("/scenes")[0].startswith("Scenes")


def test_wrong_accusation_ends_the_game(case):
    game, _ = make_game(case)
    game.handle("/accuse mina")
    game.handle("jealousy")
    game.handle("poison")
    out = game.handle("E01")
    assert any("CASE FAILED" in line for line in out)
    assert "It was Pintu Kamat." in out
