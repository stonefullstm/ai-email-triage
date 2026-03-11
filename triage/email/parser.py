import email
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime

# import re


from .models import EmailMessage


class EmailParser:

    def parse(self, raw_email: bytes) -> EmailMessage:
        """
        Parses a raw email message and extracts its components
        into an EmailMessage object.
        """
        msg = email.message_from_bytes(raw_email)

        subject = self._decode_header(msg.get("Subject"))
        sender = msg.get("From")
        # sender = re.sub(r"\[([^\]]+)\]\(mailto:[^\)]+\)", r"\1", sender)
        to = msg.get("To")
        date = self._parse_date(msg.get("Date"))
        body = self._extract_body(msg)

        return EmailMessage(
            subject=subject or "",
            sender=sender or "",
            to=to,
            date=date,
            body=body
        )

    def _decode_header(self, value):

        if not value:
            return ""
        try:
            subject = str(make_header(decode_header(value)))
        except (LookupError, UnicodeDecodeError, ValueError):
            try:
                decoded = decode_header(value)[0]
                part, encoding = decoded
                if isinstance(part, bytes):
                    enc = encoding or "utf-8"
                    if enc == "unknown-8bit":
                        enc = "latin-1"
                    subject = part.decode(enc, errors="replace")
                else:
                    subject = part
            except Exception:
                subject = value.encode(
                    "latin-1", errors="ignore").decode("latin-1")
        return subject

    def _parse_date(self, value):

        if not value:
            return None

        try:
            return parsedate_to_datetime(value)
        except Exception:
            return None

    def _extract_body(self, msg):

        if msg.is_multipart():

            for part in msg.walk():

                content_type = part.get_content_type()
                disposition = str(part.get("Content-Disposition"))

                if (content_type == "text/plain" and "attachment"
                        not in disposition):

                    payload = part.get_payload(decode=True)

                    if payload:
                        return payload.decode("utf-8", errors="replace")

        else:

            payload = msg.get_payload(decode=True)

            if payload:
                return payload.decode("utf-8", errors="replace")

        return ""
