from backend.schemas.case_models import (
    CaseBible, Fact, FactKnowledge, Character, EvidenceItem, Solution,
)
from backend.validation.case_validator import validate_case


def make_case() -> CaseBible:
    return CaseBible(
        id="CASE01",
        title="Test Case",
        facts=[
            Fact(id="F01", text="Mara was at the boathouse at 21:40.", people=["mara"]),
            Fact(id="F02", text="Theo was in the kitchen.", people=["theo"]),
        ],
        timeline=["F02", "F01"],
        characters=[
            Character(
                id="mara", name="Mara", persona="Proud ferry owner",
                knowledge=[FactKnowledge(fact_id="F01", status="lies", cover_story="I was home all night.")],
            ),
            Character(id="theo", name="Theo", persona="Nervous cook",
                      knowledge=[FactKnowledge(fact_id="F02", status="knows")]),
        ],
        evidence=[
            EvidenceItem(id="E01", name="Wet boots", description="Muddy boots by the door.",
                         proves=["F01"], scene="boathouse"),
        ],
        solution=Solution(culprit_id="mara", motive="Money", method="Pushed", evidence_chain=["E01"]),
    )


def has_error(errors, text):
    return any(text in e for e in errors)


def test_valid_case_has_no_errors():
    assert validate_case(make_case()) == []


def test_duplicate_fact_id():
    case = make_case()
    case.facts.append(Fact(id="F01", text="Duplicate."))
    assert has_error(validate_case(case), "duplicate fact id: F01")


def test_timeline_unknown_fact():
    case = make_case()
    case.timeline.append("F99")
    assert has_error(validate_case(case), "timeline references unknown fact F99")


def test_fact_unknown_character():
    case = make_case()
    case.facts[1].people = ["ghost"]
    assert has_error(validate_case(case), "unknown character ghost")


def test_lie_without_cover_story():
    case = make_case()
    case.characters[0].knowledge[0].cover_story = None
    assert has_error(validate_case(case), "no cover_story")


def test_evidence_unknown_fact():
    case = make_case()
    case.evidence[0].proves = ["F99"]
    assert has_error(validate_case(case), "E01 proves unknown fact F99")


def test_evidence_proves_nothing():
    case = make_case()
    case.evidence[0].proves = []
    assert has_error(validate_case(case), "proves no facts")


def test_unknown_culprit():
    case = make_case()
    case.solution.culprit_id = "nobody"
    assert has_error(validate_case(case), "not a character")


def test_empty_evidence_chain():
    case = make_case()
    case.solution.evidence_chain = []
    assert has_error(validate_case(case), "no evidence chain")


def test_culprit_hides_nothing():
    case = make_case()
    case.characters[0].knowledge = []
    assert has_error(validate_case(case), "hides nothing")


def test_chain_never_reaches_culprit():
    case = make_case()
    case.evidence[0].proves = ["F02"]  # fact about Theo, not Mara
    assert has_error(validate_case(case), "involving the culprit")

def test_fact_missing_from_timeline():
    case = make_case()
    case.timeline.remove("F02")
    assert has_error(validate_case(case), "Fact not mentioned in the timeline F02")


def test_duplicate_fact_in_timeline():
    case = make_case()
    case.timeline.append("F01")
    assert has_error(validate_case(case), "duplicate Fact in timeline: F01")


def test_unreachable_fact():
    case = make_case()
    case.facts.append(Fact(id="F03", text="Nobody can reveal this."))
    case.timeline.append("F03")
    assert has_error(validate_case(case), "F03: no evidence proves it")