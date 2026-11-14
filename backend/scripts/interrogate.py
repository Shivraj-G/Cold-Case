from backend.validation.case_validator import confirm_case
from backend.llm.provider import OllamaProvider
from backend.agents.responds import respond
from backend.agents.context_builder import build_context
llm = OllamaProvider()

def interrogate(context,messages):
    FORBIDDEN = ["instructions", "prompt", "AI", "language model"]
    FALLBACK = "I'd rather not talk about that."

    try:
        result = respond(llm, context, messages, FORBIDDEN, FALLBACK)
        return result
    except Exception as er:
        return f"Error: {er}" 


def main():
    casefile = confirm_case("case01")
    messages = {"mina":[],"pintu":[],"vishwas":[],"santosh":[]}
    contextfile = {}
    while True:
        suspect = input("suspect: ")
        if suspect == "quit":
            break
        if suspect.strip() in messages:
            if suspect not in contextfile.keys():
                context = build_context(casefile,suspect)
                contextfile[suspect] = context
            while True:
                user = input("ask: ")
                if user == "next":
                    break
                else:
                    messages[suspect].append({"role":"user","content":user})
                    reply = interrogate(contextfile[suspect],messages[suspect])
                    if "Error" in reply.text:
                        print(reply.text)
                    else:
                        messages[suspect].append({"role":"assistant","content":reply.text})
                        print(reply.text)

main()
