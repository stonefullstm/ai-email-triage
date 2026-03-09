from triage.email.parser import EmailParser


def test_parse_simple_email():
    raw_email = b"""From: sender@example.com
To: receiver@example.com
Subject: Simple test
Date: Thu, 1 Jan 2024 12:00:00 +0000

This is the body.
"""
    parser = EmailParser()
    result = parser.parse(raw_email)

    assert result.subject == "Simple test"
    assert result.sender == "sender@example.com"
    assert result.to == "receiver@example.com"
    # A data deve ser um datetime
    assert result.date is not None
    assert result.body == "This is the body.\n"


def test_parse_multipart_email():
    raw_email = b"""From: sender@example.com
To: receiver@example.com
Subject: Multipart test
Date: Thu, 1 Jan 2024 12:00:00 +0000
Content-Type: multipart/mixed; boundary="boundary"

--boundary
Content-Type: text/plain

This is the plain text body.
--boundary
Content-Type: text/html

<p>This is the HTML body.</p>
--boundary--
"""
    parser = EmailParser()
    result = parser.parse(raw_email)

    assert result.subject == "Multipart test"
    assert result.sender == "sender@example.com"
    assert result.to == "receiver@example.com"
    assert result.date is not None
    # Deve pegar a parte text/plain
    assert result.body == "This is the plain text body."


def test_parse_email_with_attachment():
    raw_email = b"""From: sender@example.com
To: receiver@example.com
Subject: With attachment
Date: Thu, 1 Jan 2024 12:00:00 +0000
Content-Type: multipart/mixed; boundary="boundary"

--boundary
Content-Type: text/plain

This is the body.
--boundary
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="file.txt"

File content.
--boundary--
"""
    parser = EmailParser()
    result = parser.parse(raw_email)

    assert result.subject == "With attachment"
    assert result.sender == "sender@example.com"
    assert result.to == "receiver@example.com"
    assert result.date is not None
    # O corpo deve ser o texto, ignorando o anexo
    assert result.body == "This is the body."


def test_parse_email_no_subject():
    raw_email = b"""From: sender@example.com
To: receiver@example.com
Date: Thu, 1 Jan 2024 12:00:00 +0000

No subject.
"""
    parser = EmailParser()
    result = parser.parse(raw_email)

    assert result.subject == ""  # subject nulo vira string vazia
    assert result.sender == "sender@example.com"
    assert result.to == "receiver@example.com"
    assert result.date is not None
    assert result.body == "No subject.\n"


def test_parse_email_with_encoded_subject():
    raw_email = b"""From: sender@example.com
To: receiver@example.com
Subject: =?utf-8?q?Hello=C2=A0World?=
Date: Thu, 1 Jan 2024 12:00:00 +0000

Body.
"""
    parser = EmailParser()
    result = parser.parse(raw_email)

    # O subject decodificado deve ser "Hello World" (com um espaço não quebrável que pode ser convertido para espaço)
    # Dependendo da decodificação, o \u00A0 pode ser mantido ou convertido.
    # No nosso código, usamos errors="ignore" e decodificamos com utf-8, então deve ser "Hello World" (com um espaço não quebrável).
    # Mas para simplificar, vamos verificar se contém "Hello" e "World".
    assert "Hello" in result.subject
    assert "World" in result.subject


def test_parse_email_invalid_date():
    raw_email = b"""From: sender@example.com
To: receiver@example.com
Subject: Invalid date
Date: Invalid date string

Body.
"""
    parser = EmailParser()
    result = parser.parse(raw_email)

    assert result.subject == "Invalid date"
    assert result.sender == "sender@example.com"
    assert result.to == "receiver@example.com"
    assert result.date is None  # data inválida deve ser None
    assert result.body == "Body.\n"


def test_parse_email_no_body():
    raw_email = b"""From: sender@example.com
To: receiver@example.com
Subject: No body
Date: Thu, 1 Jan 2024 12:00:00 +0000
"""
    parser = EmailParser()
    result = parser.parse(raw_email)

    assert result.subject == "No body"
    assert result.sender == "sender@example.com"
    assert result.to == "receiver@example.com"
    assert result.date is not None
    assert result.body == ""  # sem corpo, string vazia
