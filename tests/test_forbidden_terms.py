import pytest

from backend.agents.guard import forbidden_terms
from backend.schemas.case_models import (
    CaseBible, Fact, FactKnowledge, Character, EvidenceItem, Solution,
)


def make_keyword_case() -> CaseBible:
    return CaseBible(
        id="K",
        title="Keyword case",
        public_info=["Ramesh was strangled in his flat."],
        facts=[
            Fact(id="F01", text="Theo cooked in the kitchen.", keywords=["kitchen"]),
            Fact(id="F02", text="Mara met a buyer at the pier.", keywords=["pier"]),
            Fact(id="F03", text="Mara hid a ledger.", keywords=["ledger"]),
            Fact(id="F04", text="He was strangled with a cord.", keywords=["strangled"]),
        ],
        timeline=["F01", "F02", "F03", "F04"],
        characters=[
            Character(id="theo", name="Theo", persona="Nervous cook",
                      knowledge=[FactKnowledge(fact_id="F01", status="knows")]),
            Character(id="mara", name="Mara", persona="Proud ferry owner",
                      knowledge=[FactKnowledge(fact_id="F03", status="hides")]),
        ],
        evidence=[EvidenceItem(id="E01", name="Cord", description="A cord.",
                               proves=["F04"], scene="flat")],
        solution=Solution(culprit_id="mara", motive="m", method="m", evidence_chain=["E01"]),
    )


def test_known_fact_keyword_is_allowed():
    assert "kitchen" not in forbidden_terms(make_keyword_case(), "theo")


def test_unknown_fact_keyword_is_forbidden():
    assert "kitchen" in forbidden_terms(make_keyword_case(), "mara")
    assert "pier" in forbidden_terms(make_keyword_case(), "theo")


def test_hidden_fact_keyword_is_forbidden():
    assert "ledger" in forbidden_terms(make_keyword_case(), "mara")


def test_public_info_keyword_is_removed():
    case = make_keyword_case()
    assert "strangled" not in forbidden_terms(case, "theo")
    assert "strangled" not in forbidden_terms(case, "mara")


def test_unknown_suspect_raises():
    with pytest.raises(ValueError):
        forbidden_terms(make_keyword_case(), "nobody")