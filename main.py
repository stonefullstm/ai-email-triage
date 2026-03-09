from triage.email.imap_reader import IMAPReader
from triage.core.pipeline import ClassificationPipeline
from triage.core.base import EmailInput
from triage.core.hash_cache import HashCacheLayer
from triage.core.embedding import EmbeddingLayer
from triage.core.heuristics import HeuristicLayer
from triage.core.llm_fallback import LLMFallbackLayer
from triage.core.rules_loader import load_rules
from triage.email.parser import EmailParser
from triage.embedder.model import Embedder
from triage.llm.ollama_client import OllamaClient
from dotenv import load_dotenv
import os
load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME", "qwen2.5:7b")
LABELS = ["financeiro", "spam", "notificacao", "pessoal"]

hash_cache = HashCacheLayer()


# def build_pipeline() -> ClassificationPipeline:
#     return ClassificationPipeline(layers=[
#         hash_cache,
#         EmbeddingLayer(encoder=Embedder()),
#         HeuristicLayer(rules=load_rules()),
#         LLMFallbackLayer(
#             model=MODEL_NAME,
#             client=OllamaClient(),
#             labels=LABELS,
#         ),
#     ])
def build_pipeline() -> ClassificationPipeline:
    print("⏳ Carregando embedder...", flush=True)
    embedder = Embedder()
    print("✅ Embedder pronto.", flush=True)

    print("⏳ Carregando regras...", flush=True)
    rules = load_rules()
    print("✅ Regras prontas.", flush=True)

    return ClassificationPipeline(layers=[
        hash_cache,
        EmbeddingLayer(encoder=embedder),
        HeuristicLayer(rules=rules),
        LLMFallbackLayer(client=OllamaClient(), labels=LABELS),
    ])


def build_reader() -> IMAPReader:
    return IMAPReader(
        host=os.environ["IMAP_SERVER"],
        username=os.environ["MAIL_ACCOUNT"],
        password=os.environ["EMAIL_PASSWORD"],
    )


def run():
    reader = build_reader()
    parser = EmailParser()
    core = build_pipeline()

    print("⏳ Conectando ao IMAP...", flush=True)
    reader.connect()
    print("✅ Conectado.", flush=True)

    print("⏳ Buscando e-mails não lidos...", flush=True)
    emails = reader.fetch_unseen()
    print(f"✅ {len(emails)} e-mail(s) encontrado(s).", flush=True)

    if not emails:
        print("Nenhum e-mail não lido.")
        return

    for raw_email in emails:
        parsed = parser.parse(raw_email)
        email = EmailInput(
            subject=parsed.subject,
            sender=parsed.sender,
            body=parsed.body,
        )

        result = core.run(email)

        if result:
            print(
                f"[{result.source.upper()}] {email.subject[:60]!r} → "
                f"{result.label} ({result.confidence:.0%})"
            )
            # retroalimenta o cache com classificações confiantes
            if result.confidence >= 0.90:
                hash_cache.store(email, result.label)
        else:
            print(f"[SEM CLASSIFICAÇÃO] {email.subject[:60]!r}")


if __name__ == "__main__":
    run()
