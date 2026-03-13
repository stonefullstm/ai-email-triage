"""CLI interface for AI E-mail Triage system."""
import logging
from pathlib import Path
from typing import Optional, Annotated
from importlib.metadata import version as pkg_version
import functools

import typer
from dotenv import load_dotenv

import triage
from triage.config.app_config import AppConfig
from triage.email.imap_reader import IMAPReader
from triage.email.parser import EmailParser
from triage.core.pipeline import ClassificationPipeline
from triage.core.base import EmailInput
from triage.core.hash_cache import HashCacheLayer
from triage.core.embedding import EmbeddingLayer
from triage.data.embedding_store import EmbeddingStore
from triage.data.classification_store import ClassificationStore
from triage.data.processed_store import ProcessedStore
from triage.core.heuristics import HeuristicLayer
from triage.core.llm_fallback import LLMFallbackLayer
from triage.core.rules_loader import load_rules
from triage.embedder.model import Embedder
from triage.llm.ollama_client import OllamaClient
from triage.cli.exceptions import TriageCliException

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("triage")

# Version
try:
    __version__ = pkg_version("ai-triage")
except Exception:
    __version__ = "0.1.0"


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        typer.echo(f"triage version {__version__}")
        raise typer.Exit()


app = typer.Typer(
    name="triage",
    help="AI E-mail Triage — layered e-mail classification with LLM fallback",
    no_args_is_help=True,
)


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            "-v",
            help="Show version and exit",
            callback=version_callback,
        ),
    ] = None,
) -> None:
    """
    AI E-mail Triage system.

    Classifies incoming emails using a multi-stage pipeline:
    1. Heuristics (rules and keywords)
    2. Semantic similarity (embeddings)
    3. LLM fallback (when uncertain)

    Configure required environment variables in .env:
    - IMAP_SERVER: IMAP server address (e.g., imap.gmail.com)
    - MAIL_ACCOUNT: Email account username
    - EMAIL_PASSWORD: Email password or app password
    - MODEL_NAME: LLM model name (optional, default: qwen2.5:7b)
    """
    pass


# Helper: error handler decorator
def handle_cli_errors(func):
    """Decorator to handle and format CLI exceptions."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except TriageCliException as e:
            typer.secho(f"❌ Error: {e.message}", fg=typer.colors.RED)
            logger.error(
                f"{e.__class__.__name__}: {e.message}",
                exc_info=logger.isEnabledFor(logging.DEBUG),
            )
            raise typer.Exit(code=e.exit_code)
        except KeyboardInterrupt:
            typer.secho("\n⏸ Cancelled by user", fg=typer.colors.YELLOW)
            raise typer.Exit(code=130)
        except Exception as e:
            typer.secho(
                f"❌ Unexpected error: {type(e).__name__}: {str(e)}",
                fg=typer.colors.RED,
            )
            logger.exception("Unexpected error occurred")
            raise typer.Exit(code=1)

    return wrapper


hash_cache = HashCacheLayer()
classification_store = ClassificationStore()
processed_store = ProcessedStore()


def build_pipeline(
        config: AppConfig, skip_llm: bool = False) -> ClassificationPipeline:
    layers = [
        hash_cache,
        EmbeddingLayer(encoder=Embedder()),
        HeuristicLayer(rules=load_rules()),
    ]
    if not skip_llm:
        layers.append(
            LLMFallbackLayer(client=OllamaClient(), labels=config.llm.labels))
    return ClassificationPipeline(layers=layers)


def build_reader(config: AppConfig, mailbox: str) -> IMAPReader:
    return IMAPReader(
        host=config.imap.server,
        username=config.imap.username,
        password=config.imap.password,
        mailbox=mailbox,
    )


def get_source_color(source):
    """Returns ANSI color for the font."""
    source_colors = {
        "cache": typer.colors.CYAN,
        "embedding": typer.colors.BLUE,
        "heuristic": typer.colors.YELLOW,
        "llm": typer.colors.MAGENTA,
    }
    return source_colors.get(source, typer.colors.WHITE)


def parse_bytes_to_email_input(parser: EmailParser, raw: bytes) -> EmailInput:
    """Converts raw bytes to EmailInput."""
    parsed = parser.parse(raw)
    return EmailInput(
        subject=parsed.subject,
        sender=parsed.sender,
        body=parsed.body,
    )


def parse_path_to_email_input(parser: EmailParser, path: Path) -> EmailInput:
    """Reads file and converts to EmailInput."""
    raw = path.read_bytes()
    return parse_bytes_to_email_input(parser, raw)


def process_single_email(path: Path, pipeline, parser):
    """Processes a single e-mail file."""
    typer.echo(f"\n📧 Processing: {path.name}")
    email_input = parse_path_to_email_input(parser, path)

    typer.echo(f"  📧 Sender: {email_input.sender}")
    typer.echo(f"  📋 Subject: {email_input.subject}")
    typer.echo("  📝 Body (first lines):")
    for line in email_input.body.splitlines()[:3]:
        typer.echo(f"    {line[:70]}")
    typer.echo("")

    result = pipeline.run(email_input)
    print_result(result)

    if result and result.confidence >= 0.90:
        hash_cache.store(email_input, result.label)


def process_email_folder(folder: Path, pipeline, parser):
    """Processes all .eml/.txt files in a folder."""
    email_files = list(folder.glob("*.eml")) + list(folder.glob("*.txt"))

    if not email_files:
        typer.secho(
            "❌ No .eml or .txt file found in the folder.", fg=typer.colors.RED)
        return

    typer.echo(
        f"📁 Processing {len(email_files)} e-mail(s) in '{folder.name}':\n")

    stats = {}

    for path in email_files:
        email_input = parse_path_to_email_input(parser, path)

        result = pipeline.run(email_input)
        stats.setdefault(result.label if result else "sem_classificacao", 0)
        stats[result.label if result else "sem_classificacao"] += 1

        short_subject = email_input.subject[:50]
        if result:
            source_tag = typer.style(
                f"[{result.source.upper()}]",
                fg=get_source_color(result.source)
            )
            typer.echo(f"{source_tag} {short_subject} → {result.label}")
        else:
            typer.echo(
                typer.style("[UNCLASSIFIED]",
                            fg=typer.colors.RED) + f" {short_subject}"
            )

        if result and result.confidence >= 0.90:
            hash_cache.store(email_input, result.label)

    typer.echo("\n📊 Summary:")
    for label, count in sorted(stats.items()):
        typer.echo(f"  {label}: {count}")


def print_result(result):
    """Prints classification result."""
    if result:
        color = get_source_color(result.source)
        source_tag = typer.style(
            f"[{result.source.upper()}]", fg=color, bold=True)
        typer.echo(f"{source_tag} → {result.label} ({result.confidence:.0%})")
        if result.metadata.get("reason"):
            typer.echo(f"💬 Reason: {result.metadata['reason']}")
    else:
        typer.secho("[UNCLASSIFIED]", fg=typer.colors.RED)


@app.command()
@handle_cli_errors
def run(
    limit: int = typer.Option(
        10, "--limit", "-l", help="Maximum number of e-mails to process."
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
    config = AppConfig.from_env()
    logger.info(f"Starting classification run: limit={limit}, days={days}")
    typer.echo("⏳ Loading pipeline...")
    pipeline = build_pipeline(config=config, skip_llm=skip_llm)
    parser = EmailParser()

    typer.echo("⏳ Connecting to IMAP...")
    reader = build_reader(config=config, mailbox=mailbox)
    reader.connect()

    typer.echo(
        f"⏳ Searching for e-mails (last {days} day(s), limit {limit})...")
    raw_emails = reader.fetch_unseen(days=days, limit=limit)

    if not raw_emails:
        typer.echo("✅ No unread e-mails found.")
        raise typer.Exit()

    new_emails = []
    skipped = 0
    for raw in raw_emails:
        parsed = parser.parse(raw)
        if processed_store.is_processed(parsed.message_id):
            skipped += 1
            continue
        new_emails.append(parsed)

    if skipped:
        typer.echo(
            f"⏭  {skipped} e-mail(s) já processado(s) anteriormente, "
            f"ignorado(s)."
        )

    if not new_emails:
        typer.secho(
            "✅ Nenhum e-mail novo para processar.", fg=typer.colors.GREEN)
        raise typer.Exit()

    typer.echo(f"📬 {len(new_emails)} e-mail(s) found.\n")

    for parsed in new_emails:
        email_input = EmailInput(
            subject=parsed.subject,
            sender=parsed.sender,
            body=parsed.body,
        )
        result = pipeline.run(email_input)

        if result:
            classification_store.add(
                result.label,
                result.source,
                result.confidence,
                email_input.subject,
                email_input.sender,
            )
            processed_store.mark(
                parsed.message_id, result.label, result.source)
            color = get_source_color(result.source)
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
        None, help="Path to the rules.yaml file."
    ),
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
    path: str = typer.Argument(
        ..., help="File .eml/.txt or folder with various e-mails."
    ),
    skip_llm: bool = typer.Option(False, "--skip-llm"),
):
    """Classify an e-mail or all e-mails in a folder."""
    config = AppConfig.from_env()
    from pathlib import Path

    base_path = Path(triage.__file__).parent / path
    pipeline = build_pipeline(config=config, skip_llm=skip_llm)
    parser = EmailParser()

    if base_path.is_file():
        # Single file
        process_single_email(base_path, pipeline, parser)
    elif base_path.is_dir():
        # Folder with multiple e-mails
        process_email_folder(base_path, pipeline, parser)
    else:
        typer.secho(f"❌ Path not found: {base_path}", fg=typer.colors.RED)
        raise typer.Exit(1)


@app.command()
def review(
    days: int = typer.Option(
        1, "--days", "-d", help="Search e-mails from last N days."
    ),
    limit: int = typer.Option(
        20, "--limit", "-l", help="Maximum number of e-mails to process."
    ),
    mailbox: str = typer.Option("INBOX", "--mailbox", "-m"),
    skip_llm: bool = typer.Option(False, "--skip-llm"),
):
    """Reviews recent e-mails and annotates examples
    for the embedding database."""
    config = AppConfig.from_env()
    logger.info(f"Starting review run: limit={limit}, days={days}")
    typer.echo("⏳ Loading pipeline...")
    pipeline = build_pipeline(config=config, skip_llm=skip_llm)
    parser = EmailParser()
    store = EmbeddingStore()
    embedder = Embedder()

    reader = build_reader(config=config, mailbox=mailbox)
    reader.connect()
    raw_emails = reader.fetch_unseen(days=days, limit=limit)

    if not raw_emails:
        typer.secho("✅ Nenhum e-mail encontrado.", fg=typer.colors.GREEN)
        raise typer.Exit()

    new_emails = []
    skipped = 0
    for raw in raw_emails:
        parsed = parser.parse(raw)
        if processed_store.is_processed(parsed.message_id):
            skipped += 1
            continue
        new_emails.append(parsed)

    if skipped:
        typer.echo(f"⏭  {skipped} já processado(s), ignorado(s).")

    saved = 0
    skipped = 0

    # Extract labels from config for dynamic options
    labels = config.llm.labels

    for i, parsed in enumerate(new_emails, 1):
        email_input = EmailInput(
            subject=parsed.subject,
            sender=parsed.sender,
            body=parsed.body,
        )
        result = pipeline.run(email_input)

        typer.echo(f"\n{'─' * 60}")
        typer.echo(f"[{i}/{len(raw_emails)}]")
        typer.echo(f"  📧 Sender : {email_input.sender}")
        typer.echo(f"  📋 Subject: {email_input.subject}")
        typer.echo(f"  📝 Body   : {email_input.body[:120].strip()!r}")

        if result:
            color = get_source_color(result.source)
            suggestion = typer.style(result.label, fg=color, bold=True)
            typer.echo(
                f"\n  🤖 Suggestion: {suggestion}"
                f" ({result.source}, {result.confidence:.0%})"
            )
        else:
            typer.echo("\n  🤖 Suggestion: none")

        # Dynamically build options from LABELS
        options_str = "/".join(labels) + "/SKIP"
        default = result.label if result else None
        default_str = f" ({default})" if default else ""

        label_input = (
            typer.prompt(
                f"\n  Label [{options_str}]{default_str}",
                default=default or "SKIP",
            )
            .strip()
            .upper()
        )
        if label_input == "SKIP" or label_input not in labels:
            typer.secho("  ⏭  Skipped.", fg=typer.colors.BRIGHT_BLACK)
            skipped += 1
            continue

        # Save on cache and examples database
        hash_cache.store(email_input, label_input)
        vector = embedder.encode(
            f"{email_input.subject} {email_input.sender} {email_input.body}"
        )
        store.add(email_input, label_input, vector)
        processed_store.mark(parsed.message_id, label_input, "REVIEW")

        typer.secho(f"  ✅ Saved like '{label_input}'.", fg=typer.colors.GREEN)
        saved += 1

    typer.echo(f"\n{'─' * 60}")
    typer.secho(
        f"\n📚 Review done: {saved} saved(s), {skipped} skipped(s). "
        f"Total in database: {store.count()}",
        fg=typer.colors.GREEN,
    )


if __name__ == "__main__":
    app()
