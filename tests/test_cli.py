import pytest
from typer.testing import CliRunner
from triage.cli import app
from triage.cli.exceptions import ConfigError
from triage.config.app_config import AppConfig

runner = CliRunner()


class TestVersion:
    """Tests for version command."""

    def test_version_flag(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.stdout.lower()

    def test_version_short_flag(self):
        result = runner.invoke(app, ["-v"])
        assert result.exit_code == 0


class TestHelp:
    """Tests for help system."""

    def test_main_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "AI E-mail Triage" in result.stdout

    def test_run_help(self):
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        assert "--limit" in result.stdout
        assert "--days" in result.stdout


class TestConfigValidation:
    """Tests for configuration validation."""

    def test_missing_env_vars(self, monkeypatch):
        """Test that ConfigError is raised when env vars are missing."""
        # Remove required env vars
        monkeypatch.delenv("IMAP_SERVER", raising=False)
        monkeypatch.delenv("MAIL_ACCOUNT", raising=False)
        monkeypatch.delenv("EMAIL_PASSWORD", raising=False)

        with pytest.raises(ConfigError) as exc_info:
            AppConfig.from_env()

        assert "Missing required environment variables" in str(exc_info.value)


class TestArgumentValidation:
    """Tests for argument validation."""

    def test_limit_min_boundary(self, monkeypatch):
        """Test that limit must be >= 1."""
        monkeypatch.setenv("IMAP_SERVER", "test.server")
        monkeypatch.setenv("MAIL_ACCOUNT", "test@test.com")
        monkeypatch.setenv("EMAIL_PASSWORD", "password")

        result = runner.invoke(app, ["run", "--limit", "0"])
        # Typer validates automatically
        assert result.exit_code != 0

    def test_days_max_boundary(self, monkeypatch):
        """Test that days must be <= 365."""
        monkeypatch.setenv("IMAP_SERVER", "test.server")
        monkeypatch.setenv("MAIL_ACCOUNT", "test@test.com")
        monkeypatch.setenv("EMAIL_PASSWORD", "password")

        result = runner.invoke(app, ["run", "--days", "366"])
        assert result.exit_code != 0


class TestCheckRules:
    """Tests for check-rules command."""

    def test_check_rules_help(self):
        result = runner.invoke(app, ["check-rules", "--help"])
        assert result.exit_code == 0
        assert "Path to the rules.yaml file" in result.stdout

    def test_check_rules_no_file(self):
        """Test that error is raised when rules.yaml is missing."""
        with runner.isolated_filesystem():
            result = runner.invoke(app, ["check-rules", "rules.yaml"])
            assert result.exit_code != 0
            assert (
                "no such file or directory: 'rules.yaml'"
                in result.stdout.lower()
                or "file not found: 'rules.yaml'" in result.stdout.lower()
            )
