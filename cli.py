import os
import typer
from dotenv import load_dotenv
from typing import Optional

from triage.email.imap_reader import IMAPReader
from triage.email.parser import EmailParser
from triage.core.pipeline import ClassificationPipeline
from triage.core.base import EmailInput
from triage.core.hash_cache import HashCacheLayer
from triage.core.embedding import EmbeddingLayer
from triage.core.heuristics import HeuristicLayer
from triage.core.llm_fallback import LLMFallbackLayer
from triage.core.rules_loader import load_rules
from triage.embedder import Embedder
from triage.llm.ollama_client import OllamaClient

load_dotenv()

app = typer.Typer(help="AI Triage — classificador de e-mails em camadas.")

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
