import hashlib
from typing import Optional
from triage.core.base import ClassifierLayer, ClassificationResult, EmailInput


class HashCacheLayer(ClassifierLayer):
    def __init__(self):
        self._cache: dict[str, str] = {}  # hash -> label

    def _hash(self, email: EmailInput) -> str:
        key = f"{email.subject}|{email.sender}"
        return hashlib.sha256(key.encode()).hexdigest()

    def classify(self, email: EmailInput) -> Optional[ClassificationResult]:
        key = self._hash(email)
        label = self._cache.get(key)
        if label:
            return ClassificationResult(
                label=label,
                confidence=1.0,  # cache é determinístico
                source="cache",
                metadata={"hash": key},
            )
        return None

    def store(self, email: EmailInput, label: str) -> None:
        """Retroalimenta o cache com uma classificação confirmada."""
        key = self._hash(email)
        self._cache[key] = label
