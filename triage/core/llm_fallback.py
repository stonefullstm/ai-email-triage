from typing import Optional
from triage.core.base import ClassifierLayer, ClassificationResult, EmailInput


PROMPT_TEMPLATE = """
Você é um classificador de e-mails.
Analise o e-mail abaixo e retorne APENAS o label mais adequado
dentre as categorias disponíveis.

Categorias disponíveis: {labels}

E-mail:
- Remetente: {sender}
- Assunto: {subject}
- Corpo: {body}

Responda com um JSON no formato:
{{"label": "<categoria>",
  "confidence": <0.0 a 1.0>,
  "reason": "<justificativa curta>"}}
""".strip()


class LLMFallbackLayer(ClassifierLayer):
    THRESHOLD = 0.70  # mais permissivo por ser o último recurso

    def __init__(self, client, labels: list[str], model: str = "qwen2.5:7b"):
        """
        client: qualquer objeto com método chat(model, prompt) -> str
                compatível com Ollama, OpenAI, etc.
        labels: lista de categorias possíveis
        model:  nome do modelo a usar
        """
        self.client = client
        self.labels = labels
        self.model = model

    def classify(self, email: EmailInput) -> Optional[ClassificationResult]:
        prompt = PROMPT_TEMPLATE.format(
            labels=", ".join(self.labels),
            sender=email.sender,
            subject=email.subject,
            body=email.body[:500],  # limita o corpo para economizar tokens
        )

        try:
            raw = self.client.chat(model=self.model, prompt=prompt)
            return self._parse_response(raw)
        except Exception as e:
            return ClassificationResult(
                label="indefinido",
                confidence=0.0,
                source="llm",
                metadata={"error": str(e)},
            )

    def _parse_response(self, raw: str) -> ClassificationResult:
        import json
        import re

        match = re.search(r"\{.*?\}", raw, re.DOTALL)
        if not match:
            raise ValueError(f"Resposta fora do formato esperado: {raw}")

        data = json.loads(match.group())

        return ClassificationResult(
            label=data["label"],
            confidence=float(data["confidence"]),
            source="llm",
            metadata={"reason": data.get("reason", "")},
        )
