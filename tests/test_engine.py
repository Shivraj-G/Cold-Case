import pytest

from backend.game.engine import (
    GameState, PresentResult, band, collect, present_evidence, questions_left, record, scenes,
    QUESTION_LIMIT,
)
from backend.validation.case_validator import confirm_case


@pytest.fixture
def state():
    return GameState(case=confirm_case("case01"))


def test_bands():
    assert band(0) == "calm"
    assert band(29) == "calm"
    assert band(30) == "defensive"
    assert band(60) == "breaking"
    assert band(100) == "breaking"


def test_scenes_listed(state):
    assert scenes(state.case) == ["flat_3b", "lobby", "police_records"]


def test_collect_scene_finds_items_once(state):
    first = collect(state, "lobby")
    assert sorted(e.id for e in first) == ["E03", "E04", "E10"]
    assert collect(state, "lobby") == []
    assert {"E03", "E04", "E10"} <= state.found


def test_cannot_show_evidence_you_do_not_have(state):
    result = present_evidence(state, "pintu", "E06")
    assert result.ok is False
    assert state.stress == {}


def test_unknown_evidence_is_not_ok(state):
    assert present_evidence(state, "pintu", "E99").ok is False


def test_calm_suspect_feels_half_the_stress(state):
    collect(state, "flat_3b")
    result = present_evidence(state, "pintu", "E06")   # exposes 1 fact; Pintu is "calm": 30 * 0.5
    assert result.ok and len(result.exposed) == 1
    assert result.stress == 15
    assert result.band == "calm"


def test_pintu_breaks_after_enough_evidence(state):
    collect(state, "police_records")
    first = present_evidence(state, "pintu", "E07")    # 2 facts: 30
    assert first.stress == 30 and first.band == "defensive" and first.broke is False
    second = present_evidence(state, "pintu", "E09")   # 2 more facts: 60
    assert second.stress == 60 and second.band == "breaking" and second.broke is True


def test_same_evidence_twice_adds_nothing(state):
    collect(state, "police_records")
    present_evidence(state, "pintu", "E07")
    again = present_evidence(state, "pintu", "E07")
    assert again.exposed == []
    assert again.stress == 30


def test_irrelevant_evidence_adds_no_stress(state):
    collect(state, "lobby")
    result = present_evidence(state, "pintu", "E04")   # the rider's records say nothing about Pintu
    assert result.ok and result.exposed == [] and result.stress == 0


def test_santosh_breaks_on_one_item(state):
    collect(state, "lobby")
    result = present_evidence(state, "santosh", "E10")   # 3 facts: 90
    assert result.stress == 90 and result.broke is True


def test_stress_is_capped_at_100(state):
    collect(state, "lobby")
    collect(state, "police_records")
    collect(state, "flat_3b")
    for ev in ("E03", "E05", "E06", "E07", "E08", "E09", "E10"):
        for sid in ("mina", "pintu", "vishwas", "santosh"):
            present_evidence(state, sid, ev)
    assert all(v <= 100 for v in state.stress.values())


def test_present_to_witness_or_unknown_raises(state):
    collect(state, "lobby")
    with pytest.raises(ValueError):
        present_evidence(state, "deepak", "E04")
    with pytest.raises(ValueError):
        present_evidence(state, "nobody", "E04")


def test_ledger_and_question_limit(state):
    assert questions_left(state, "pintu") == QUESTION_LIMIT
    s1 = record(state, "pintu", "where were you?", "At home.")
    s2 = record(state, "pintu", "alone?", "Yes.")
    assert (s1.turn, s2.turn) == (1, 2)
    assert questions_left(state, "pintu") == QUESTION_LIMIT - 2
    assert questions_left(state, "mina") == QUESTION_LIMIT
    assert [s.suspect_id for s in state.ledger] == ["pintu", "pintu"]
