import pytest

from backend.game.scoring import score_accusation
from backend.validation.case_validator import confirm_case

FOUND = {"E06", "E07", "E08", "E09", "E01"}
MOTIVE = "He was committing fraud and Ramesh was going to report it to management."
METHOD = "He strangled him with a cord after being let in during the blackout."


@pytest.fixture(scope="module")
def case():
    return confirm_case("case01")


def test_perfect_accusation(case):
    s = score_accusation(case, "pintu", MOTIVE, METHOD, ["E06", "E07", "E08"], FOUND)
    assert (s.culprit, s.motive, s.method, s.evidence, s.total) == (40, 20, 20, 20, 100)
    assert s.verdict == "CASE SOLVED"


def test_wrong_culprit_scores_nothing_else(case):
    s = score_accusation(case, "mina", MOTIVE, METHOD, ["E06", "E07", "E08"], FOUND)
    assert s.total == 0 and s.verdict == "CASE FAILED"


def test_partial_motive_and_method(case):
    s = score_accusation(case, "pintu", "He was stealing money.", "He used a cord.", [], FOUND)
    assert s.motive == 10 and s.method == 10 and s.evidence == 0
    assert s.total == 60 and s.verdict == "PARTIAL RESULT"


def test_empty_answers(case):
    s = score_accusation(case, "pintu", "", "", [], FOUND)
    assert s.total == 40


def test_evidence_must_be_found_unique_and_capped(case):
    assert score_accusation(case, "pintu", "", "", ["E06", "E06", "E06"], FOUND).evidence == 7
    assert score_accusation(case, "pintu", "", "", ["E06", "E07"], {"E06"}).evidence == 7
    assert score_accusation(case, "pintu", "", "", ["E09", "E08", "E07", "E06"], FOUND).evidence == 20


def test_irrelevant_evidence_is_noted_and_not_counted(case):
    s = score_accusation(case, "pintu", "", "", ["E01", "E06"], FOUND)
    assert s.evidence == 7 and s.notes


def test_whole_words_only(case):
    # "report" must not be matched inside "reporter", "cord" not inside "accord"
    s = score_accusation(case, "pintu", "a reporter story", "in accord", [], FOUND)
    assert s.motive == 0 and s.method == 0
