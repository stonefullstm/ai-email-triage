# test_imap_reader.py

import pytest
from unittest.mock import patch
import email
from email import policy
from email.message import EmailMessage
from email.header import Header
from datetime import datetime, timedelta

from triage.email.imap_reader import IMAPReader


@pytest.fixture
def reader():
    return IMAPReader("imap.example.com", "user", "pass", mailbox="INBOX")


def make_email(subject="Assunto", sender="from@example.com", body="Corpo"):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg.set_content(body)
    return msg


@patch("triage.email.imap_reader.imaplib.IMAP4_SSL")
def test_connect_calls_imap_correctly(mock_imap, reader):
    mock_conn = mock_imap.return_value
    reader.connect()

    mock_imap.assert_called_once_with("imap.example.com")
    mock_conn.login.assert_called_once_with("user", "pass")
    mock_conn.select.assert_called_once_with("INBOX")
    assert reader.conn is mock_conn


@patch("triage.email.imap_reader.imaplib.IMAP4_SSL")
def test_fetch_unseen_no_messages(mock_imap, reader):
    mock_conn = mock_imap.return_value
    # connect
    reader.connect()

    # search sem IDs
    mock_conn.search.return_value = ("OK", [b""])

    emails = reader.fetch_unseen()
    since = (datetime.now() - timedelta(days=1)).strftime('%d-%b-%Y')
    mock_conn.search.assert_called_once_with(
        None, f'(UNSEEN SINCE {since})')
    assert emails == []


@patch("triage.email.imap_reader.imaplib.IMAP4_SSL")
def test_fetch_unseen_single_simple_email(mock_imap, reader):
    mock_conn = mock_imap.return_value
    reader.connect()

    # search com um ID
    mock_conn.search.return_value = ("OK", [b"1"])

    # construir mensagem simples
    msg = make_email(
        subject="Assunto teste",
        sender="remetente@example.com",
        body="Olá mundo"
    )
    raw_bytes = msg.as_bytes()

    # fetch devolve estrutura típica: [(b'1 (RFC822 {len})', raw_bytes)]
    mock_conn.fetch.return_value = (
        "OK",
        [(bytes("1 (RFC822 {0})".format(len(raw_bytes)).encode()), raw_bytes)],
    )

    emails = reader.fetch_unseen()

    assert len(emails) == 1
    email_data = email.message_from_bytes(emails[0], policy=policy.default)
    print(email_data)
    assert email_data["subject"] == "Assunto teste"
    assert email_data["from"] == "remetente@example.com"
    assert "Olá mundo" in email_data.get_content()


@patch("triage.email.imap_reader.imaplib.IMAP4_SSL")
def test_fetch_unseen_multipart_email_usa_text_plain(mock_imap, reader):
    mock_conn = mock_imap.return_value
    reader.connect()

    mock_conn.search.return_value = ("OK", [b"1"])

    # e-mail multipart com text/plain e text/html
    msg = EmailMessage()
    msg["Subject"] = "Multipart"
    msg["From"] = "multi@example.com"
    msg.set_content("Texto simples")  # text/plain
    msg.add_alternative("<p>HTML</p>", subtype="html")
    raw_bytes = msg.as_bytes()

    mock_conn.fetch.return_value = ("OK", [(b"1 (RFC822)", raw_bytes)])

    emails = reader.fetch_unseen()
    assert len(emails) == 1
    email_data = email.message_from_bytes(emails[0], policy=policy.default)
    for part in email_data.walk():
        if part.get_content_type() == "text/plain":
            assert "Texto simples" in part.get_payload(decode=True).decode()
        elif part.get_content_type() == "text/html":
            assert "HTML" in part.get_payload(decode=True).decode()


@patch("triage.email.imap_reader.imaplib.IMAP4_SSL")
def test_parse_email_with_encoded_subject(mock_imap, reader):
    mock_conn = mock_imap.return_value
    reader.connect()

    mock_conn.search.return_value = ("OK", [b"1"])

    # assunto com encoding, ex: utf-8
    subject_text = "Assunto com acentos: çãõ"
    msg = EmailMessage()
    msg["Subject"] = Header(subject_text, "utf-8").encode()
    msg["From"] = "encoded@example.com"
    msg.set_content("Corpo")
    raw_bytes = msg.as_bytes()

    mock_conn.fetch.return_value = ("OK", [(b"1 (RFC822)", raw_bytes)])

    emails = reader.fetch_unseen()
    assert len(emails) == 1
    email_data = email.message_from_bytes(emails[0], policy=policy.default)
    assert email_data["subject"] == subject_text
    assert email_data["from"] == "encoded@example.com"
    assert "Corpo" in email_data.get_content()
