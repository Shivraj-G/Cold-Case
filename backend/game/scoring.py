from dataclasses import dataclass, field

from backend.agents.guard import contains_word
from backend.schemas.case_models import CaseBible

CULPRIT_POINTS = 40
MOTIVE_POINTS = 20
METHOD_POINTS = 20
EVIDENCE_POINTS = 20
MAX_EVIDENCE = 3
SOLVED_AT = 80
PARTIAL_AT = 50


@dataclass
class Score:
    culprit: int = 0
    motive: int = 0
    method: int = 0
    evidence: int = 0
    notes: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.culprit + self.motive + self.method + self.evidence

    @property
    def verdict(self) -> str:
        if self.total >= SOLVED_AT:
            return "CASE SOLVED"
        if self.total >= PARTIAL_AT:
            return "PARTIAL RESULT"
        return "CASE FAILED"


def score_text(answer: str, groups: list[list[str]], points: int) -> int:
    """Each group is the synonyms for one required idea. Points are split evenly across groups."""
    if not groups:
        return 0
    hit = sum(1 for group in groups if any(contains_word(term, answer) for term in group))
    return round(points * hit / len(groups))


def score_accusation(
    case: CaseBible,
    culprit_id: str,
    motive: str,
    method: str,
    evidence_ids: list[str],
    found: set[str],
) -> Score:
    sol = case.solution
    score = Score()

    if culprit_id != sol.culprit_id:
        score.notes.append("Wrong person. Motive, method and evidence cannot count for someone else.")
        return score
    score.culprit = CULPRIT_POINTS

    score.motive = score_text(motive, sol.motive_keys, MOTIVE_POINTS)
    score.method = score_text(method, sol.method_keys, METHOD_POINTS)

    # only evidence you actually found counts, each item once, at most MAX_EVIDENCE of them
    cited = []
    for eid in evidence_ids:
        if eid in found and eid not in cited:
            cited.append(eid)
    cited = cited[:MAX_EVIDENCE]
    needed = min(MAX_EVIDENCE, len(sol.evidence_chain))
    good = [e for e in cited if e in sol.evidence_chain]
    score.evidence = round(EVIDENCE_POINTS * min(len(good), needed) / needed) if needed else 0
    if len(good) < len(cited):
        score.notes.append("Some of the evidence you cited does not prove the case against them.")
    return score
