from backend.validation.case_validator import confirm_case
from backend.llm.provider import OllamaProvider
from backend.agents.responds import respond
from backend.agents.context_builder import build_context
llm = OllamaProvider()

def interrogate(casefile,suspect_id,messages):
    FORBIDDEN = ["instructions", "prompt", "AI", "language model"]
    FALLBACK = "I'd rather not talk about that."

    context = build_context(casefile,suspect_id)
    try:
        result = respond(llm, context, messages, FORBIDDEN, FALLBACK)
        return result
    except Exception as er:
        return f"Error: {er}" 


def main():
    casefile = confirm_case("case01")
    messages = {"mina":[],"pintu":[],"vishwas":[],"santosh":[]}
    suspect = input("suspect: ")

    while True:
        user = input("ask: ")
        if user == "quit":
            break
        else:
            messages[suspect].append({"role":"user","content":user})
            reply = interrogate(casefile,suspect,messages[suspect])
            if "Error" in reply.text:
                print(reply.text)
            else:
                messages[suspect].append({"role":"assistant","content":reply.text})
                print(reply.text)

main()
