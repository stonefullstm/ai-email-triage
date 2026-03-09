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
        """
        Return cached classification if email hash exists in cache.

        Checks the internal cache using a SHA256 hash of the email's subject
        and sender. If a matching hash is found, returns a
        ClassificationResult with confidence 1.0. Otherwise returns None,
        indicating no cached classification available.
        """
        key = self._hash(email)
        label = self._cache.get(key)
        if label:
            return ClassificationResult(
                label=label,
                confidence=1.0,  # cache is deterministic
                source="cache",
                metadata={"hash": key},
            )
        return None

    def store(self, email: EmailInput, label: str) -> None:
        """Feedback the cache with a confirmed classification."""
        key = self._hash(email)
        self._cache[key] = label
