from pathlib import Path
import yaml
from triage.core.heuristics import HeuristicRule


def load_rules(
    path: str | Path = "triage/config/rules.yaml",
) -> list[HeuristicRule]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return [
        HeuristicRule(
            label=rule["label"],
            confidence=rule["confidence"],
            senders=rule.get("senders", []),
            subject_patterns=rule.get("subject_patterns", []),
            body_patterns=rule.get("body_patterns", []),
        )
        for rule in data["rules"]
    ]
