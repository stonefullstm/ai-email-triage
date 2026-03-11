import os
from pathlib import Path
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
from triage.core.embedding_store import EmbeddingStore
from triage.core.heuristics import HeuristicLayer
from triage.core.llm_fallback import LLMFallbackLayer
from triage.core.rules_loader import load_rules
from triage.embedder.model import Embedder
from triage.llm.ollama_client import OllamaClient

load_dotenv()

app = typer.Typer(
    help="AI E-mail Triage — layered e-mail classification with LLM fallback")

MODEL_NAME = os.getenv("MODEL_NAME", "qwen2.5:7b")
# LABELS = ["financeiro", "spam", "notificacao", "pessoal"]
LABELS = [
    "ACTION_REQUIRED", "REVIEW_RECOMMENDED", "FYI_IGNORE", "REFERENCE_ONLY"]
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


def get_source_color(source):
    """Returns ANSI color for the font."""
    source_colors = {
        "cache":     typer.colors.CYAN,
        "embedding": typer.colors.BLUE,
        "heuristic": typer.colors.YELLOW,
        "llm":       typer.colors.MAGENTA,
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
            typer.echo(typer.style(
                    "[UNCLASSIFIED]",
                    fg=typer.colors.RED) + f" {short_subject}")

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

    for raw in raw_emails:
        email_input = parse_bytes_to_email_input(parser, raw)

        result = pipeline.run(email_input)

        if result:
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
    path: str = typer.Argument(
        ..., help="File .eml/.txt or folder with various e-mails."),
    skip_llm: bool = typer.Option(False, "--skip-llm"),
):
    """Classify an e-mail or all e-mails in a folder."""
    from pathlib import Path

    base_path = Path(triage.__file__).parent / path
    pipeline = build_pipeline(skip_llm=skip_llm)
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
        1, "--days", "-d", help="Search e-mails from last N days."),
    limit: int = typer.Option(
        20, "--limit", "-l", help="Maximum number of e-mails to process."),
    mailbox: str = typer.Option("INBOX", "--mailbox", "-m"),
    skip_llm: bool = typer.Option(False, "--skip-llm"),
):
    """Reviews recent e-mails and annotates examples
       for the embedding database."""

    pipeline = build_pipeline(skip_llm=skip_llm)
    parser = EmailParser()
    store = EmbeddingStore()
    embedder = Embedder()

    reader = build_reader(mailbox)
    reader.connect()
    raw_emails = reader.fetch_unseen(days=days, limit=limit)

    if not raw_emails:
        typer.secho("✅ Nenhum e-mail encontrado.", fg=typer.colors.GREEN)
        raise typer.Exit()

    saved = 0
    skipped = 0

    for i, raw in enumerate(raw_emails, 1):
        email_input = parse_bytes_to_email_input(parser, raw)
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

        # monta as opções dinamicamente a partir dos LABELS
        options_str = "/".join(LABELS) + "/SKIP"
        default = result.label if result else None
        default_str = f" ({default})" if default else ""

        label_input = typer.prompt(
            f"\n  Label [{options_str}]{default_str}",
            default=default or "SKIP",
        ).strip().upper()
        if label_input == "SKIP" or label_input not in LABELS:
            typer.secho("  ⏭  Skipped.", fg=typer.colors.BRIGHT_BLACK)
            skipped += 1
            continue

        # salva no cache e no banco de exemplos
        hash_cache.store(email_input, label_input)
        vector = embedder.encode(
            f"{email_input.subject} {email_input.sender} {email_input.body}"
        )
        store.add(email_input, label_input, vector)

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
