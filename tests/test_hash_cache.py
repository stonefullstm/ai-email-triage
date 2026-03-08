import pytest
from triage.core.hash_cache import HashCacheLayer
from triage.core.base import EmailInput


@pytest.fixture
def layer():
    return HashCacheLayer()


@pytest.fixture
def email():
    return EmailInput(
        subject="Fatura de Janeiro",
        sender="banco@example.com",
        body="Segue sua fatura.",
    )


def test_classify_returns_none_when_cache_empty(layer, email):
    assert layer.classify(email) is None


def test_store_and_classify_returns_correct_label(layer, email):
    layer.store(email, "financeiro")
    result = layer.classify(email)

    assert result is not None
    assert result.label == "financeiro"
    assert result.confidence == 1.0
    assert result.source == "cache"


def test_classify_returns_none_for_different_subject(layer, email):
    layer.store(email, "financeiro")

    other = EmailInput(
        subject="Boleto de Fevereiro",
        sender="banco@example.com",
        body="Segue seu boleto.",
    )
    assert layer.classify(other) is None


def test_classify_returns_none_for_different_sender(layer, email):
    layer.store(email, "financeiro")

    other = EmailInput(
        subject="Fatura de Janeiro",
        sender="outro@example.com",
        body="Segue sua fatura.",
    )
    assert layer.classify(other) is None


def test_store_overwrites_existing_label(layer, email):
    layer.store(email, "financeiro")
    layer.store(email, "spam")

    result = layer.classify(email)
    assert result.label == "spam"


def test_is_confident_always_true_for_cache_result(layer, email):
    layer.store(email, "financeiro")
    result = layer.classify(email)
    assert layer.is_confident(result)
