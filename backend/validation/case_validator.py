from backend.schemas.case_models import CaseBible

def validate_case(case: CaseBible) -> list[str]:

    errors: list[str] = []

    fact_ids = [f.id for f in case.facts]
    char_ids = [c.id for c in case.characters]
    evidence_ids = [e.id for e in case.evidence]

    #ids must be unique
    for label, ids in (("fact", fact_ids), ("character", char_ids), ("evidence", evidence_ids)):
        for dup in sorted({i for i in ids if ids.count(i) > 1}):
            errors.append(f"duplicate {label} id: {dup}")

    facts, chars = set(fact_ids), set(char_ids)

    #timeline must only use real facts
    for fid in case.timeline:
        if fid not in facts:
            errors.append(f"timeline references unknown fact {fid}")

    #all facts are i the timeline
    for fact in case.facts:
        if fact.id not in case.timeline:
            errors.append(f"Fact not mentioned in the timeline {fact.id}")
    for dup in sorted({i for i in case.timeline if case.timeline.count(i)>1}):
            errors.append(f"duplicate Fact in timeline: {dup}")

    #facts should be proven by evidence or characters
    proven_by_evidence = {fid for ev in case.evidence for fid in ev.proves}
    known_by_someone = {k.fact_id for ch in case.characters for k in ch.knowledge}
    for fid in fact_ids:
        if fid not in proven_by_evidence and fid not in known_by_someone:
            errors.append(f"{fid}: no evidence proves it and no character knows it")

    #facts must only involve real characters
    for fact in case.facts:
        for person in fact.people:
            if person not in chars:
                errors.append(f"{fact.id} lists unknown character {person}")

    #knowledge entries must point at real facts; lies need a cover story
    for ch in case.characters:
        for k in ch.knowledge:
            if k.fact_id not in facts:
                errors.append(f"{ch.id} has knowledge of unknown fact {k.fact_id}")
            if k.status.value == "lies" and not k.cover_story:
                errors.append(f"{ch.id} lies about {k.fact_id} but has no cover_story")
            if k.status.value == "lies" and not k.asked_about:
                errors.append(f"{ch.id} lies about {k.fact_id} but has no asked_about")

    #evidence must prove something real
    for ev in case.evidence:
        if not ev.proves:
            errors.append(f"{ev.id} proves no facts")
        for fid in ev.proves:
            if fid not in facts:
                errors.append(f"{ev.id} proves unknown fact {fid}")

    #the solution must be made of real parts
    sol = case.solution
    if sol.culprit_id not in chars:
        errors.append(f"culprit {sol.culprit_id} is not a character")
    if not sol.evidence_chain:
        errors.append("solution has no evidence chain")
    for eid in sol.evidence_chain:
        if eid not in set(evidence_ids):
            errors.append(f"evidence chain references unknown evidence {eid}")

    #solvability: a player must be able to reach the culprit
    culprit = next((c for c in case.characters if c.id == sol.culprit_id), None)
    if culprit:
        if not any(k.status.value in ("hides", "lies") for k in culprit.knowledge):
            errors.append("culprit hides nothing, so there is nothing to uncover")

        by_id = {f.id: f for f in case.facts}
        proven = {
            fid
            for ev in case.evidence if ev.id in sol.evidence_chain
            for fid in ev.proves
        }
        if not any(sol.culprit_id in by_id[fid].people for fid in proven if fid in by_id):
            errors.append("no evidence in the chain proves a fact involving the culprit")

    return errors

def confirm_case(casename):

    path = "cases/"+casename+".json"
    with open(path,'r',encoding="utf-8") as casefile:
        case = casefile.read()

    this_case = CaseBible.model_validate_json(case)

    errors = validate_case(this_case)
    
    if errors:
        return ("Errors in the case: ",errors)
    else: return this_case

if __name__ == "__main__":
    confirm_case()