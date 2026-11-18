import requests

from backend.agents.context_builder import build_context
from backend.agents.guard import forbidden_terms
from backend.agents.responds import respond
from backend.llm.provider import OllamaProvider
from backend.validation.case_validator import confirm_case

GLOBAL_TERMS = ["instructions", "prompt", "AI", "language model"]
FALLBACK = "I'd rather not talk about that."
MAX_HISTORY = 10  # last messages sent to the model; keeps a 3B model inside its context


def start_suspect(case, suspect_id):
    """Everything that stays fixed for one suspect: their prompt, forbidden terms and history."""
    return {
        "context": build_context(case, suspect_id),
        "terms": GLOBAL_TERMS + forbidden_terms(case, suspect_id),
        "history": [],
    }


def ask(llm, session, question):
    """Send one question. Returns a GuardedReply, or None if the model could not be reached."""
    history = session["history"]
    history.append({"role": "user", "content": question})
    try:
        result = respond(
            llm, session["context"], history[-MAX_HISTORY:], session["terms"], FALLBACK
        )
    except requests.RequestException as err:
        history.pop()  # do not keep a question that never got an answer
        print(f"[model unreachable: {err}]")
        return None
    history.append({"role": "assistant", "content": result.text})
    return result


def main():
    llm = OllamaProvider()
    case = confirm_case("case01")
    suspects = [c.id for c in case.characters if c.role == "suspect"]
    sessions = {}

    print("Suspects:", ", ".join(suspects), "| 'next' switches suspect, 'quit' exits")
    while True:
        name = input("suspect: ").strip().lower()
        if name == "quit":
            break
        if name not in suspects:
            print(f"Pick one of: {', '.join(suspects)}")
            continue
        if name not in sessions:
            sessions[name] = start_suspect(case, name)

        while True:
            question = input(f"ask {name}: ").strip()
            if not question:
                continue
            if question == "next":
                break
            if question == "quit":
                return
            result = ask(llm, sessions[name], question)
            if result is None:
                continue
            print(result.text)
            if result.used_fallback:
                print(f"  [guard blocked: {result.flags}]")


if __name__ == "__main__":
    main()