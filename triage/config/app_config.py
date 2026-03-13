import os
from dataclasses import dataclass
from typing import Optional
from triage.cli.exceptions import ConfigError


@dataclass
class IMAPConfig:
    """IMAP server configuration."""

    server: str
    username: str
    password: str

    @classmethod
    def from_env(cls) -> "IMAPConfig":
        """Load IMAP configuration from environment variables.

        Raises:
            ConfigError: If any required variable is missing.
        """
        required_vars = {
            "IMAP_SERVER": "server",
            "MAIL_ACCOUNT": "username",
            "EMAIL_PASSWORD": "password",
        }

        missing = []
        values = {}

        for env_var, field_name in required_vars.items():
            value = os.getenv(env_var)
            if not value:
                missing.append(env_var)
            else:
                values[field_name] = value

        if missing:
            raise ConfigError(
                f"Missing required environment variables: "
                f"{', '.join(missing)}. "
                f"Please set them in .env file or export them."
            )

        return cls(**values)


@dataclass
class LLMConfig:
    """LLM configuration."""

    model_name: str
    labels: list[str]

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Load LLM configuration from environment variables and rules.yaml."""
        from pathlib import Path
        from triage.core.rules_loader import load_rules

        rules_path = Path(__file__).parent / "rules.yaml"
        rules = load_rules(rules_path)
        # Extract unique labels from rules, sorted for consistency
        labels = sorted(set(rule.label for rule in rules))
        return cls(
            model_name=os.getenv("MODEL_NAME", "qwen2.5:7b"),
            labels=labels,
        )


@dataclass
class AppConfig:
    """Main application configuration."""

    llm: LLMConfig
    imap: Optional[IMAPConfig] = None
    debug: bool = False

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load complete configuration from environment variables."""
        return cls(
            llm=LLMConfig.from_env(),
            imap=IMAPConfig.from_env(),
            debug=os.getenv("DEBUG", "").lower() == "true",
        )

    @classmethod
    def llm_from_env(cls) -> "AppConfig":
        """Load only LLM configuration (no IMAP required)."""
        return cls(
            llm=LLMConfig.from_env(),
            imap=None,
            debug=os.getenv("DEBUG", "").lower() == "true",
        )
