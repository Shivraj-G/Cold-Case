import re

from backend.schemas.case_models import CaseBible


def contains_word(term: str, text: str) -> bool:
    """True if term appears in text as a whole word or phrase, ignoring case."""
    return re.search(rf"\b{re.escape(term)}\b", text, re.IGNORECASE) is not None


def check_reply(reply: str, forbidden: list[str]) -> list[str]:
    """Return the forbidden terms that appear in the reply as whole words."""
    flags = []
    for word in forbidden:
        term = word.strip()
        if not term:
            continue  # an empty term would match everything
        if contains_word(term, reply):
            flags.append(term)
    return flags


def forbidden_terms(case: CaseBible, suspect_id: str) -> list[str]:
    """Keywords this suspect must not say: facts they do not know, hide, or lie about."""
    character = next((c for c in case.characters if c.id == suspect_id), None)
    if character is None:
        raise ValueError(f"unknown character: {suspect_id}")

    facts = {f.id: f for f in case.facts}
    known_ids = {k.fact_id for k in character.knowledge if k.status.value == "knows"}

    terms = {
        kw.strip()
        for fact in case.facts if fact.id not in known_ids
        for kw in fact.keywords
        if kw.strip()
    }

    lies = [k for k in character.knowledge if k.status.value == "lies"]
    allowed_text = " ".join([
        character.persona,
        " ".join(character.traits),
        " ".join(case.public_info),
        *(facts[fid].text for fid in known_ids),
        *(k.cover_story for k in lies if k.cover_story),
        *(k.asked_about for k in lies if k.asked_about),
    ])

    return sorted(t for t in terms if not contains_word(t, allowed_text))