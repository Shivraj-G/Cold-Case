from backend.validation.case_validator import confirm_case
from backend.llm.provider import OllamaProvider
from backend.agents.context_builder import build_context
llm = OllamaProvider()

def Interrogate(case,suspect_id):
    casefile = confirm_case(case)
    context = build_context(casefile,suspect_id)
    messages = [{"role":"user","content":"where were you on saturday night?"}]
    reply = llm.chat(context,messages)
    print(reply)

Interrogate("case01","pintu")