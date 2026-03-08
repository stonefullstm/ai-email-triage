import pytest
from triage.core.heuristics import HeuristicLayer, HeuristicRule
from triage.core.base import EmailInput


@pytest.fixture
def rules():
    return [
        HeuristicRule(
            label="financeiro",
            confidence=0.90,
            senders=["banco@example.com"],
            subject_patterns=[r"fatura", r"boleto"],
        ),
        HeuristicRule(
            label="spam",
            confidence=0.95,
            subject_patterns=[r"ganhe", r"grátis"],
            body_patterns=[r"unsubscribe"],
        ),
    ]


@pytest.fixture
def layer(rules):
    return HeuristicLayer(rules=rules)


def test_match_by_sender(layer):
    email = EmailInput(subject="Olá", sender="banco@example.com", body="Texto")
    result = layer.classify(email)

    assert result is not None
    assert result.label == "financeiro"
    assert result.source == "heuristic"
    assert "sender:" in result.metadata["matched_by"]


def test_match_by_subject_pattern(layer):
    email = EmailInput(
        subject="Sua fatura chegou",
        sender="outro@example.com",
        body=""
    )
    result = layer.classify(email)

    assert result is not None
    assert result.label == "financeiro"
    assert "subject:" in result.metadata["matched_by"]


def test_match_by_body_pattern(layer):
    email = EmailInput(
        subject="Newsletter",
        sender="news@example.com",
        body="Clique para unsubscribe"
    )
    result = layer.classify(email)

    assert result is not None
    assert result.label == "spam"
    assert "body:" in result.metadata["matched_by"]


def test_subject_match_is_case_insensitive(layer):
    email = EmailInput(subject="BOLETO VENCENDO", sender="x@x.com", body="")
    result = layer.classify(email)

    assert result is not None
    assert result.label == "financeiro"


def test_no_match_returns_none(layer):
    email = EmailInput(
        subject="Reunião amanhã",
        sender="colega@example.com",
        body="Tudo certo?"
    )
    assert layer.classify(email) is None


def test_first_matching_rule_wins(layer):
    # sender bate na regra "financeiro" antes de checar "spam"
    email = EmailInput(
        subject="ganhe prêmios",
        sender="banco@example.com",
        body=""
    )
    result = layer.classify(email)

    assert result.label == "financeiro"


def test_confidence_is_propagated(layer):
    email = EmailInput(subject="fatura", sender="x@x.com", body="")
    result = layer.classify(email)

    assert result.confidence == 0.90


def test_is_confident_respects_threshold(layer):
    email = EmailInput(subject="fatura", sender="x@x.com", body="")
    result = layer.classify(email)

    assert layer.is_confident(result)  # 0.90 >= 0.85
