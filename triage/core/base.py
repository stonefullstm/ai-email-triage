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
    """Interface base para todas as camadas do pipeline."""

    THRESHOLD: float = 0.85

    @abstractmethod
    def classify(self, email: EmailInput) -> Optional[ClassificationResult]:
        """
        Tenta classificar o e-mail.
        Retorna ClassificationResult se confiante o suficiente,
        ou None para passar para a próxima camada.
        """
        ...

    def is_confident(self, result: ClassificationResult) -> bool:
        return result.confidence >= self.THRESHOLD
