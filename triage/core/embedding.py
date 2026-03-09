import numpy as np
from typing import Optional
from triage.core.base import ClassifierLayer, ClassificationResult, EmailInput


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


class EmbeddingLayer(ClassifierLayer):
    def __init__(self, encoder, top_k: int = 3):
        """
        encoder: any object with an encode(text: str) -> np.ndarray method
                 ex: SentenceTransformer, local model, external API
        top_k:   how many neighbors to consider for majority voting
        """
        self.encoder = encoder
        self.top_k = top_k
        self._examples: list[tuple[np.ndarray, str]] = []  # (vetor, label)

    def add_example(self, email: EmailInput, label: str) -> None:
        """Adds an annotated example to the reference database."""
        vector = self._encode(email)
        self._examples.append((vector, label))

    def classify(self, email: EmailInput) -> Optional[ClassificationResult]:
        if not self._examples:
            return None

        vector = self._encode(email)
        scored = [
            (cosine_similarity(vector, ex_vec), label)
            for ex_vec, label in self._examples
        ]
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[: self.top_k]

        label = self._majority_vote(top)
        confidence = float(np.mean([score for score, _ in top if _ == label]))

        return ClassificationResult(
            label=label,
            confidence=confidence,
            source="embedding",
            metadata={
              "top_k": [{"label": l, "score": round(s, 4)} for s, l in top]
            },
        )

    def _encode(self, email: EmailInput) -> np.ndarray:
        text = f"{email.subject} {email.sender} {email.body}"
        return self.encoder.encode(text)

    def _majority_vote(self, top: list[tuple[float, str]]) -> str:
        votes: dict[str, float] = {}
        for score, label in top:
            votes[label] = votes.get(label, 0.0) + score
        return max(votes, key=lambda label: votes[label])
