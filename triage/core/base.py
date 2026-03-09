from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EmailInput:
    subject: str
    sender: str
    body: str
    raw: Optional[dict] = field(default=None)


@dataclass
class ClassificationResult:
    label: str
    confidence: float
    source: str
    metadata: dict = field(default_factory=dict)


class ClassifierLayer(ABC):
    """Base interface for all layers in the pipeline."""

    THRESHOLD: float = 0.85

    @abstractmethod
    def classify(self, email: EmailInput) -> Optional[ClassificationResult]:
        """
        Tries to classify the email.
        Returns ClassificationResult if confident enough,
        or None to pass to the next layer.
        """
        ...

    def is_confident(self, result: ClassificationResult) -> bool:
        return result.confidence >= self.THRESHOLD
