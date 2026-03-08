from typing import Optional
from triage.core.base import ClassifierLayer, ClassificationResult, EmailInput


class ClassificationPipeline:
    def __init__(self, layers: list[ClassifierLayer]):
        self.layers = layers

    def run(self, email: EmailInput) -> Optional[ClassificationResult]:
        for layer in self.layers:
            result = layer.classify(email)
            if result and layer.is_confident(result):
                return result
        return None  # nenhuma camada teve confiança suficiente
