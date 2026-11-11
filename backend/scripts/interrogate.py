from backend.validation.case_validator import confirm_case
from backend.llm.provider import OllamaProvider
from backend.agents.context_builder import build_context
llm = OllamaProvider()

def interrogate(casefile,suspect_id,messages):

    context = build_context(casefile,suspect_id)
    try:
        reply = llm.chat(context,messages)
        return reply
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
            messages[suspect].append({"role":"assistant","content":reply})
            print(reply)

main()
