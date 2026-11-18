import pytest

from backend.agents.context_builder import build_context
from backend.validation.case_validator import confirm_case


@pytest.fixture(scope="module")
def case():
    return confirm_case("case01")


def test_calm_prompt_uses_cover_story_not_truth(case):
    prompt = build_context(case, "pintu")
    assert "WHAT TO SAY WHEN ASKED" in prompt
    assert "I was at home all night." in prompt
    assert "Pintu strangles Ramesh" not in prompt            # the true fact must not be there
    assert "diverting company payments" in prompt             # the hidden fact is named, by design
    assert case.solution.motive not in prompt
    assert case.solution.method not in prompt


def test_prompt_contains_public_info(case):
    assert "He was strangled with a length of cord." in build_context(case, "mina")


def test_unknown_fact_text_never_in_prompt(case):
    prompt = build_context(case, "santosh")
    assert "battery backup" not in prompt                     # the router fact: he has no entry for it
    assert "Pintu" not in prompt


def test_defensive_adds_tone_line(case):
    assert "You feel the pressure" in build_context(case, "pintu", "defensive")
    assert "You feel the pressure" not in build_context(case, "pintu", "calm")


def test_breaking_prompt_gives_truth_and_drops_cover_story(case):
    prompt = build_context(case, "pintu", "breaking")
    assert "THE TRUTH" in prompt
    assert "Pintu strangles Ramesh with the cord he brought" in prompt
    assert "WHAT TO SAY WHEN ASKED" not in prompt
    assert "WHAT YOU ARE HIDING" not in prompt
    assert "Stop lying" in prompt


def test_victim_and_unknown_raise(case):
    with pytest.raises(ValueError):
        build_context(case, "ramesh")
    with pytest.raises(ValueError):
        build_context(case, "nobody")
