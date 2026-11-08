import pytest
from pydantic import ValidationError

from backend.schemas.case_models import (
    Knowledge,
    Fact,
    FactKnowledge,
    Character,
    EvidenceItem,
    Solution,
    CaseBible
)

# FACT TESTS
def test_valid_fact():
    fact = Fact(
        id="F01",
        text="The victim was found dead.",
        time="10:00 PM",
        place="Library",
        people=["John", "Alice"]
    )

    assert fact.id == "F01"
    assert fact.text == "The victim was found dead."
    assert fact.time == "10:00 PM"
    assert fact.place == "Library"
    assert len(fact.people) == 2


def test_fact_optional_fields():
    fact = Fact(
        id="F02",
        text="A window was left open."
    )

    assert fact.time is None
    assert fact.place is None
    assert fact.people == []


def test_fact_missing_required_field():
    with pytest.raises(ValidationError):
        Fact(id="F03")


def test_fact_invalid_people_type():
    with pytest.raises(ValidationError):
        Fact(
            id="F04",
            text="Someone entered the room.",
            people="John"
        )



# FACT KNOWLEDGE TESTS
def test_valid_fact_knowledge():
    data = FactKnowledge(
        fact_id="F01",
        status=Knowledge.KNOWS,
        cover_story="I was sleeping."
    )

    assert data.fact_id == "F01"
    assert data.status == Knowledge.KNOWS
    assert data.cover_story == "I was sleeping."


def test_all_knowledge_statuses():
    for status in Knowledge:
        data = FactKnowledge(
            fact_id="F01",
            status=status
        )

        assert data.status == status


def test_invalid_knowledge_status():
    with pytest.raises(ValidationError):
        FactKnowledge(
            fact_id="F01",
            status="unknown"
        )


def test_fact_knowledge_optional_cover_story():
    data = FactKnowledge(
        fact_id="F01",
        status="knows"
    )

    assert data.cover_story is None


# CHARACTER TESTS

def test_valid_character():
    character = Character(
        id="C01",
        name="John",
        persona="A suspicious businessman",
        traits=["proud", "anxious"]
    )

    assert character.name == "John"
    assert len(character.traits) == 2


def test_character_default_traits():
    character = Character(
        id="C02",
        name="Alice",
        persona="A quiet librarian"
    )

    assert character.traits == []


def test_character_missing_required_field():
    with pytest.raises(ValidationError):
        Character(
            id="C03",
            name="Alice"
        )


# EVIDENCE TESTS

def test_valid_evidence():
    evidence = EvidenceItem(
        id="E01",
        name="Blood-stained knife",
        description="A knife found near the victim.",
        proves=["F01", "F02"],
        scene="Library"
    )

    assert evidence.id == "E01"
    assert evidence.name == "Blood-stained knife"
    assert len(evidence.proves) == 2


def test_evidence_empty_proves():
    evidence = EvidenceItem(
        id="E02",
        name="Broken glass",
        description="Broken glass near the window.",
        proves=[],
        scene="Bedroom"
    )

    assert evidence.proves == []


def test_evidence_missing_required_field():
    with pytest.raises(ValidationError):
        EvidenceItem(
            id="E03",
            name="Footprint",
            description="A muddy footprint."
        )


# SOLUTION TESTS

def test_valid_solution():
    solution = Solution(
        culprit_id="C01",
        motive="Revenge",
        method="Poisoning",
        evidence_chain=["E01", "E02"]
    )

    assert solution.culprit_id == "C01"
    assert solution.motive == "Revenge"
    assert len(solution.evidence_chain) == 2


def test_solution_empty_evidence_chain():
    solution = Solution(
        culprit_id="C01",
        motive="Money",
        method="Theft",
        evidence_chain=[]
    )

    assert solution.evidence_chain == []


def test_solution_missing_field():
    with pytest.raises(ValidationError):
        Solution(
            culprit_id="C01",
            motive="Revenge",
            method="Poisoning"
        )


# CASE BIBLE TESTS

def test_valid_case_bible():
    case = CaseBible(
        id="CASE01",
        title="The Midnight Murder",
        facts=[
            Fact(
                id="F01",
                text="Victim found dead."
            )
        ],
        timeline=["F01"],
        characters=[
            Character(
                id="C01",
                name="John",
                persona="Businessman"
            )
        ],
        evidence=[
            EvidenceItem(
                id="E01",
                name="Knife",
                description="A bloody knife.",
                proves=["F01"],
                scene="Library"
            )
        ],
        solution=Solution(
            culprit_id="C01",
            motive="Revenge",
            method="Stabbing",
            evidence_chain=["E01"]
        )
    )

    assert case.id == "CASE01"
    assert case.title == "The Midnight Murder"
    assert len(case.facts) == 1
    assert len(case.characters) == 1
    assert len(case.evidence) == 1
    assert case.solution.culprit_id == "C01"


def test_case_bible_missing_required_field():
    with pytest.raises(ValidationError):
        CaseBible(
            id="CASE02",
            title="Incomplete Case"
        )


def test_case_bible_empty_collections():
    case = CaseBible(
        id="CASE03",
        title="Empty Case",
        facts=[],
        timeline=[],
        characters=[],
        evidence=[],
        solution=Solution(
            culprit_id="C01",
            motive="Unknown",
            method="Unknown",
            evidence_chain=[]
        )
    )

    assert case.facts == []
    assert case.timeline == []
    assert case.characters == []
    assert case.evidence == []
