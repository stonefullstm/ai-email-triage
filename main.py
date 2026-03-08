from triage.email.imap_reader import IMAPReader
from triage.core.pipeline import ClassificationPipeline
from triage.core.base import EmailInput
from triage.core.hash_cache import HashCacheLayer
from triage.core.embedding import EmbeddingLayer
from triage.core.heuristics import HeuristicLayer
from triage.core.llm_fallback import LLMFallbackLayer
from triage.core.rules_loader import load_rules
from triage.embedder.model import Embedder
from triage.llm.ollama_client import OllamaClient
from dotenv import load_dotenv
load_dotenv()


LABELS = ["financeiro", "spam", "notificacao", "pessoal"]

hash_cache = HashCacheLayer()


def build_pipeline() -> ClassificationPipeline:
    return ClassificationPipeline(layers=[
        hash_cache,
        EmbeddingLayer(encoder=Embedder()),
        HeuristicLayer(rules=load_rules()),
        LLMFallbackLayer(
            client=OllamaClient(),
            labels=LABELS,
        ),
    ])


def build_reader() -> IMAPReader:
    import os
    return IMAPReader(
        host=os.environ["IMAP_SERVER"],
        username=os.environ["MAIL_ACCOUNT"],
        password=os.environ["EMAIL_PASSWORD"],
    )


def run():
    reader = build_reader()
    core = build_pipeline()

    reader.connect()
    emails = reader.fetch_unseen()

    if not emails:
        print("Nenhum e-mail não lido.")
        return

    for raw_email in emails:
        email = EmailInput(
            subject=raw_email["subject"],
            sender=raw_email["sender"],
            body=raw_email["body"],
        )

        result = core.run(email)

        if result:
            print(f"[{result.source.upper()}] {email.subject[:60]!r} → {result.label} ({result.confidence:.0%})")
            # retroalimenta o cache com classificações confiantes
            if result.confidence >= 0.90:
                hash_cache.store(email, result.label)
        else:
            print(f"[SEM CLASSIFICAÇÃO] {email.subject[:60]!r}")


if __name__ == "__main__":
    run()
