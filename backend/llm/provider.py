import requests
from abc import ABC, abstractmethod

class LLMProvider(ABC):

    @abstractmethod
    def chat(self, system: str, messages: list[dict]) -> str:
        """Send one conversation to the model and return its reply text.

        system:   the system prompt (persona, allowed facts, rules).
        messages: the conversation so far, oldest first. Each item is a dict
                  like {"role": "user" | "assistant", "content": "..."}.
        returns:  the model's reply as plain text.
        """
        ...

class OllamaProvider(LLMProvider):
    def __init__(self, model: str = "qwen2.5:3b-instruct", base_url: str = "http://localhost:11434", timeout: int = 120):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def chat(self, system: str, messages: list[dict]) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, *messages],
            "stream": False,
        }
        response = requests.post(
            f"{self.base_url}/api/chat", json=payload, timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()["message"]["content"]

    

