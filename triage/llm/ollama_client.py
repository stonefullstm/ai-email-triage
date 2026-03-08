# triage/llm/ollama_client.py
import ollama


class OllamaClient:
    def chat(self, model: str, prompt: str) -> str:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response["message"]["content"]
