# Cold Case

A terminal detective game where the suspects are LLM agents, but the story is not improvised by the model.

Every case is a fixed, hand-authored **case bible** (facts, timeline, who knows what, evidence, solution). The LLM only *voices* a suspect. Plain Python decides what each suspect is allowed to say, how much pressure they are under, and whether your accusation is right. The result is a mystery that is fair, repeatable and solvable, with natural-language interrogation on top.

It runs fully locally on a small model (`qwen2.5` 3B via Ollama, CPU only, 8 GB RAM).

## Quick start

Requirements: Python 3.11+, [Ollama](https://ollama.com).

```bash
pip install pydantic requests pytest
ollama pull qwen2.5:3b-instruct
python -m backend.scripts.play
```

Run the tests (no model needed, they use a fake provider):

```bash
pytest
```

## How to play

Case 01 is a death in a Mumbai flat during a blackout. You start with a short public briefing. Everything else you have to find out.

| Command | What it does |
|---|---|
| `/scenes` | List places you can search |
| `/look <scene>` | Search a scene for evidence |
| `/evidence`, `/read <id>` | List and read what you have found |
| `/talk <suspect>` | Sit down with a suspect |
| *(any text)* | Ask the current suspect a question |
| `/show <id>` | Show them an evidence item |
| `/notes` | Everything they have said so far |
| `/accuse <suspect>` | Name the culprit, then give the motive, method and up to 3 pieces of evidence |

You have 15 questions per suspect, and one accusation.

Evidence is the main lever. Showing someone an item that contradicts their story raises their stress. Past a threshold they become guarded, and past another they stop lying and tell you what they were hiding. Questions alone will not get you there.

### Scoring (100 points)

| Part | Points |
|---|---|
| Right culprit | 40 |
| Motive | 20 |
| Method | 20 |
| Supporting evidence (up to 3 items from the real chain) | 20 |

A wrong culprit scores 0. 80+ is a solved case.

## How it works

```
case01.json  ->  validator  ->  CaseBible (read-only)
                                    |
        +---------------------------+---------------------------+
        |                           |                           |
  context_builder              guard (code)                 engine (code)
  one prompt per suspect,      forbidden words per          stress, bands, question
  only the facts they may      suspect and band,            limits, evidence, ledger
  say, per stress band         whole-word matching
        |                           |                           |
        +------------------>  Game session  <-------------------+
                                    |
                            LLMProvider (Ollama / fake)
```

**The model never decides the truth.** Four rules make that work:

1. **Knowledge is explicit.** Each character has an entry per fact: `knows`, `hides` or `lies`. A suspect's prompt contains only the facts they may say. For a lie, it contains the cover story and the topics it applies to, never the real fact.
2. **A code guard checks every reply.** The forbidden list is built from the keywords of facts the suspect should not know, minus anything they are legitimately allowed to say. A reply that leaks is retried once, then replaced by a canned line. Rejected replies never enter the conversation history.
3. **Stress is code, not vibes.** Each newly exposed secret adds stress. The band (calm, defensive, breaking) changes the prompt. In *breaking*, the cover story is dropped and the true facts are given to the model, so the confession is real and consistent with the bible.
4. **Accusations are scored deterministically.** Motive and method are matched against synonym groups from the case file, so grading needs no second LLM call.

Designed for a 3B model: short prompts, the key rules placed last, low temperature, a short history window, and a keyword guard instead of an LLM judge.

## Project layout

```
cases/case01.json            the case bible
backend/
  schemas/case_models.py     Pydantic models (Fact, Character, EvidenceItem, Solution, CaseBible)
  validation/                case checks and confirm_case() loader
  llm/provider.py            LLMProvider interface, OllamaProvider, FakeProvider
  agents/
    context_builder.py       builds each suspect's prompt for a stress band
    guard.py                 forbidden terms and reply checking
    responds.py              respond(): guard, retry once, fallback
  game/
    engine.py                state, stress, evidence, question limits, ledger
    scoring.py               the 100-point accusation scorer
    session.py               Game: commands in, lines out
  scripts/play.py            the terminal loop
tests/                       pytest suite
```

## Writing a new case

A case is one JSON file. The validator rejects cases that cannot be solved: unknown ids, a culprit who hides nothing, an evidence chain that never involves the culprit, evidence that "exposes" something a suspect does not actually hide, and so on. Run `confirm_case("<name>")` to check one.

The fields that matter most:

- `facts[].keywords`: words that would reveal the fact. The guard blocks them for suspects who should not know it.
- `characters[].knowledge`: `knows`, `hides` or `lies`, with a `cover_story` and `asked_about` topics for lies.
- `evidence[].exposes`: per suspect, which secrets this item breaks open.
- `solution`: culprit, motive, method, `evidence_chain`, and the `motive_keys` / `method_keys` synonym groups used for scoring.

## Known limitations

- A 3B model sometimes ignores a cover story or answers vaguely. The guard stops leaks, not dullness.
- The keyword guard only knows the words listed in the case file.
- One case so far, and a terminal UI only.

## Roadmap

- Tune prompts against the real model and add a leak-test suite
- Solvability simulation for new cases
- Small web UI 
- More cases
