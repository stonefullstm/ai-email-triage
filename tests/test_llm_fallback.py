import pytest
from unittest.mock import MagicMock
from triage.core.llm_fallback import LLMFallbackLayer
from triage.core.base import EmailInput

LABELS = ["financeiro", "spam", "notificacao", "pessoal"]


@pytest.fixture
def client():
    return MagicMock()


@pytest.fixture
def layer(client):
    return LLMFallbackLayer(client=client, labels=LABELS)


def make_email(subject="Assunto", sender="x@x.com", body="Corpo"):
    return EmailInput(subject=subject, sender=sender, body=body)


def test_classify_returns_correct_label(layer, client):
    client.chat.return_value = (
        '{"label": "financeiro", "confidence": 0.95, '
        '"reason": "menciona fatura"}'
    )

    result = layer.classify(make_email(subject="Fatura pendente"))

    assert result.label == "financeiro"
    assert result.confidence == 0.95
    assert result.source == "llm"
    assert result.metadata["reason"] == "menciona fatura"


def test_classify_handles_json_embedded_in_text(layer, client):
    client.chat.return_value = (
        'Claro! Aqui está a classificação: '
        '{"label": "spam", "confidence": 0.88, "reason": "padrão spam"}'
    )

    result = layer.classify(make_email())

    assert result.label == "spam"
    assert result.confidence == 0.88


def test_classify_returns_indefinido_on_client_exception(layer, client):
    client.chat.side_effect = ConnectionError("LLM offline")

    result = layer.classify(make_email())

    assert result.label == "indefinido"
    assert result.confidence == 0.0
    assert "error" in result.metadata


def test_classify_returns_indefinido_on_bad_json(layer, client):
    client.chat.return_value = "Não consegui classificar esse e-mail."

    result = layer.classify(make_email())

    assert result.label == "indefinido"
    assert result.confidence == 0.0


def test_body_is_truncated_to_500_chars(layer, client):
    client.chat.return_value = (
        '{"label": "pessoal", '
        '"confidence": 0.80, "reason": "ok"}'
    )
    long_body = "x" * 2000

    layer.classify(make_email(body=long_body))

    prompt_used = (
        client.chat.call_args[1]["prompt"]
        if client.chat.call_args[1] else client.chat.call_args[0][1]
    )
    assert "x" * 501 not in prompt_used


def test_threshold_is_more_permissive_than_default(layer):
    assert layer.THRESHOLD < 0.85


def test_labels_are_included_in_prompt(layer, client):
    client.chat.return_value = (
        '{"label": "pessoal", "confidence": 0.80, "reason": "ok"}'
    )

    layer.classify(make_email())

    call_args = client.chat.call_args
    prompt = call_args[0][1] if call_args[0] else call_args[1]["prompt"]
    for label in LABELS:
        assert label in prompt
