from dataclasses import dataclass, field

from backend.agents.guard import check_reply
from backend.llm.provider import LLMProvider


@dataclass
class GuardedReply:
    text: str
    used_fallback: bool = False
    flags: list[str] = field(default_factory=list)


def respond(llm: LLMProvider, 
            system: str,
            history: list[dict],
            forbidden: list[str],
            fallback: str,
            retries: int = 1,) -> GuardedReply:
    
    if retries < 0:
        raise ValueError("retries must be 0 or more")

    flags: list[str] = []
    for _ in range(retries + 1):
        reply = llm.chat(system, history)
        flags = check_reply(reply, forbidden)
        if not flags:
            return GuardedReply(text=reply)

    return GuardedReply(text=fallback, used_fallback=True, flags=flags)