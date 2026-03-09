from dataclasses import dataclass, field
import re
from typing import Optional
from triage.core.base import ClassifierLayer, ClassificationResult, EmailInput


@dataclass
class HeuristicRule:
    label: str
    confidence: float
    senders: list[str] = field(default_factory=list)       # match
    subject_patterns: list[str] = field(default_factory=list)  # regex
    body_patterns: list[str] = field(default_factory=list)     # regex


class HeuristicLayer(ClassifierLayer):
    def __init__(self, rules: list[HeuristicRule]):
        self.rules = rules

    def classify(self, email: EmailInput) -> Optional[ClassificationResult]:
        for rule in self.rules:
            matched_by = self._match(email, rule)
            if matched_by:
                return ClassificationResult(
                    label=rule.label,
                    confidence=rule.confidence,
                    source="heuristic",
                    metadata={
                        "matched_by": matched_by,
                        "rule_label": rule.label
                    },
                )
        return None

    def _match(self, email: EmailInput, rule: HeuristicRule) -> Optional[str]:
        if email.sender in rule.senders:
            return f"sender:{email.sender}"

        for pattern in rule.subject_patterns:
            if re.search(pattern, email.subject, re.IGNORECASE):
                return f"subject:{pattern}"

        for pattern in rule.body_patterns:
            if re.search(pattern, email.body, re.IGNORECASE):
                return f"body:{pattern}"

        return None
