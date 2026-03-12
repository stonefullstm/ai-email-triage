import os
from dataclasses import dataclass
# from typing import Optional
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
        """Load LLM configuration from environment variables."""
        return cls(
            model_name=os.getenv("MODEL_NAME", "qwen2.5:7b"),
            labels=[
                "ACTION_REQUIRED",
                "REVIEW_RECOMMENDED",
                "FYI_IGNORE",
                "REFERENCE_ONLY",
            ],
        )


@dataclass
class AppConfig:
    """Main application configuration."""

    imap: IMAPConfig
    llm: LLMConfig
    debug: bool = False

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load complete configuration from environment variables."""
        return cls(
            imap=IMAPConfig.from_env(),
            llm=LLMConfig.from_env(),
            debug=os.getenv("DEBUG", "").lower() == "true",
        )
