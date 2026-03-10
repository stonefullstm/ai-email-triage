import os
import typer
from dotenv import load_dotenv
from typing import Optional
import triage
from triage.email.imap_reader import IMAPReader
from triage.email.parser import EmailParser
from triage.core.pipeline import ClassificationPipeline
from triage.core.base import EmailInput
from triage.core.hash_cache import HashCacheLayer
from triage.core.embedding import EmbeddingLayer
from triage.core.heuristics import HeuristicLayer
from triage.core.llm_fallback import LLMFallbackLayer
from triage.core.rules_loader import load_rules
from triage.embedder.model import Embedder
from triage.llm.ollama_client import OllamaClient

load_dotenv()

app = typer.Typer(
    help="AI E-mail Triage — layered e-mail classification with LLM fallback")

MODEL_NAME = os.getenv("MODEL_NAME", "qwen2.5:7b")
LABELS = ["financeiro", "spam", "notificacao", "pessoal"]

hash_cache = HashCacheLayer()


def build_pipeline(skip_llm: bool = False) -> ClassificationPipeline:
    layers = [
        hash_cache,
        EmbeddingLayer(encoder=Embedder()),
        HeuristicLayer(rules=load_rules()),
    ]
    if not skip_llm:
        layers.append(LLMFallbackLayer(client=OllamaClient(), labels=LABELS))
    return ClassificationPipeline(layers=layers)


def build_reader(mailbox: str) -> IMAPReader:
    return IMAPReader(
        host=os.environ["IMAP_SERVER"],
        username=os.environ["MAIL_ACCOUNT"],
        password=os.environ["EMAIL_PASSWORD"],
        mailbox=mailbox,
    )


@app.command()
def run(
    limit: int = typer.Option(
        10, "--limit", "-l",
        help="Maximum number of e-mails to process."
    ),
    days: int = typer.Option(
        1, "--days", "-d", help="Search for e-mails from the last N days."
    ),
    mailbox: str = typer.Option(
        "INBOX", "--mailbox", "-m", help="IMAP inbox."
    ),
    skip_llm: bool = typer.Option(
        False, "--skip-llm", help="Skip the LLM layer (faster)."
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Classify without updating the cache."
    ),
):
    """Search and classify unread e-mails."""
    typer.echo("⏳ Loading pipeline...")
    pipeline = build_pipeline(skip_llm=skip_llm)
    parser = EmailParser()

    typer.echo("⏳ Connecting to IMAP...")
    reader = build_reader(mailbox)
    reader.connect()

    typer.echo(
        f"⏳ Searching for e-mails (last {days} day(s), limit {limit})...")
    raw_emails = reader.fetch_unseen(days=days, limit=limit)

    if not raw_emails:
        typer.echo("✅ No unread e-mails found.")
        raise typer.Exit()

    typer.echo(f"📬 {len(raw_emails)} e-mail(s) found.\n")

    source_colors = {
        "cache": typer.colors.CYAN,
        "embedding": typer.colors.BLUE,
        "heuristic": typer.colors.YELLOW,
        "llm": typer.colors.MAGENTA,
    }

    for raw in raw_emails:
        parsed = parser.parse(raw)
        email_input = EmailInput(
            subject=parsed.subject,
            sender=parsed.sender,
            body=parsed.body,
        )

        result = pipeline.run(email_input)

        if result:
            color = source_colors.get(result.source, typer.colors.WHITE)
            source_tag = typer.style(
                f"[{result.source.upper()}]", fg=color, bold=True)
            typer.echo(
                f"{source_tag} {email_input.subject[:60]!r} "
                f"→ {result.label} ({result.confidence:.0%})"
            )
            if not dry_run and result.confidence >= 0.90:
                hash_cache.store(email_input, result.label)
        else:
            typer.echo(
                typer.style("[UNCLASSIFIED]", fg=typer.colors.RED)
                + f" {email_input.subject[:60]!r}"
            )


@app.command()
def check_rules(
    rules_path: Optional[str] = typer.Argument(
        None, help="Path to the rules.yaml file."),
):
    """Displays the loaded heuristic rules."""
    path = rules_path or "triage/config/rules.yaml"
    rules = load_rules(path)

    typer.echo(f"📋 {len(rules)} rule(s) loaded from '{path}':\n")
    for rule in rules:
        typer.secho(
            f"  [{rule.label}] confidence={rule.confidence}", bold=True)
        if rule.senders:
            typer.echo(f"    senders:          {rule.senders}")
        if rule.subject_patterns:
            typer.echo(f"    subject_patterns: {rule.subject_patterns}")
        if rule.body_patterns:
            typer.echo(f"    body_patterns:    {rule.body_patterns}")
        typer.echo()


@app.command()
def demo(
    file: str = typer.Argument(..., help="Path to .txt file with e-mail."),
    skip_llm: bool = typer.Option(
        False, "--skip-llm", help="Skip the LLM layer."),
):
    """Classify an email from a text file."""
    from pathlib import Path

    path = Path(triage.__file__).parent / file
    if not path.exists():
        typer.secho(f"File not found: {file}", fg=typer.colors.RED)
        raise typer.Exit(1)

    raw = path.read_bytes()

    typer.echo("⏳ Loading pipeline...")
    pipeline = build_pipeline(skip_llm=skip_llm)
    parser = EmailParser()

    parsed = parser.parse(raw)
    email_input = EmailInput(
        subject=parsed.subject,
        sender=parsed.sender,
        body=parsed.body,
    )

    typer.echo(f"\n📧 Sender : {email_input.sender}")
    typer.echo(f"📋 Subject   : {email_input.subject}")
    typer.echo("📝 Body:")
    typer.echo("-" * 50)

    for line in email_input.body.splitlines()[:5]:
        typer.echo(f"  {line[:80]}")
    if len(email_input.body.splitlines()) > 5:
        typer.echo("  ... (continue)")
    typer.echo("-" * 50)
    typer.echo("")
    result = pipeline.run(email_input)

    if result:
        source_colors = {
            "cache":     typer.colors.CYAN,
            "embedding": typer.colors.BLUE,
            "heuristic": typer.colors.YELLOW,
            "llm":       typer.colors.MAGENTA,
        }
        color = source_colors.get(result.source, typer.colors.WHITE)
        source_tag = typer.style(
            f"[{result.source.upper()}]", fg=color, bold=True)
        typer.echo(f"{source_tag} → {result.label} ({result.confidence:.0%})")
        if result.metadata.get("reason"):
            typer.echo(f"💬 Reason: {result.metadata['reason']}")
    else:
        typer.secho("[UNCLASSIFIED]", fg=typer.colors.RED)


if __name__ == "__main__":
    app()
