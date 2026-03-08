import pytest
import numpy as np
from unittest.mock import MagicMock
from triage.core.embedding import EmbeddingLayer, cosine_similarity
from triage.core.base import EmailInput


def make_encoder(vectors: dict[str, np.ndarray]):
    """Encoder fake que mapeia texto -> vetor fixo."""
    encoder = MagicMock()
    encoder.encode.side_effect = lambda text: next(
        (v for k, v in vectors.items() if k in text), np.zeros(4)
    )
    return encoder


@pytest.fixture
def similar_encoder():
    """Simula vetores onde 'fatura' e 'boleto' são próximos."""
    return make_encoder(
        {
            "fatura": np.array([1.0, 0.0, 0.0, 0.0]),
            "boleto": np.array([0.9, 0.1, 0.0, 0.0]),
            "promoção": np.array([0.0, 0.0, 1.0, 0.0]),
            "reunião": np.array([0.0, 1.0, 0.0, 0.0]),
        }
    )


@pytest.fixture
def layer(similar_encoder):
    layer = EmbeddingLayer(encoder=similar_encoder, top_k=3)
    layer.add_example(
        EmailInput("fatura banco", "banco@example.com", ""), "financeiro")
    layer.add_example(
        EmailInput("boleto vence", "banco@example.com", ""), "financeiro")
    layer.add_example(
        EmailInput("promoção grátis", "spam@example.com", ""), "spam")
    return layer


def test_classify_returns_none_when_no_examples(similar_encoder):
    layer = EmbeddingLayer(encoder=similar_encoder)
    email = EmailInput("fatura", "x@x.com", "")
    assert layer.classify(email) is None


def test_classify_returns_financeiro_for_similar_email(layer):
    email = EmailInput("fatura de janeiro", "x@x.com", "")
    result = layer.classify(email)

    assert result is not None
    assert result.label == "financeiro"
    assert result.source == "embedding"


def test_classify_returns_spam_for_similar_email(layer):
    email = EmailInput("promoção imperdível", "x@x.com", "")
    result = layer.classify(email)

    assert result is not None
    assert result.label == "spam"


def test_result_has_top_k_metadata(layer):
    email = EmailInput("fatura de janeiro", "x@x.com", "")
    result = layer.classify(email)

    assert "top_k" in result.metadata
    assert len(result.metadata["top_k"]) == 3


def test_confidence_is_between_0_and_1(layer):
    email = EmailInput("fatura de janeiro", "x@x.com", "")
    result = layer.classify(email)

    assert 0.0 <= result.confidence <= 1.0


def test_cosine_similarity_identical_vectors():
    v = np.array([1.0, 0.0, 0.0])
    assert cosine_similarity(v, v) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal_vectors():
    a = np.array([1.0, 0.0])
    b = np.array([0.0, 1.0])
    assert cosine_similarity(a, b) == pytest.approx(0.0)
