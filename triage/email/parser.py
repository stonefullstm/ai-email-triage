import email
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime
import re

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
        sender = re.sub(r"\[([^\]]+)\]\(mailto:[^\)]+\)", r"\1", sender)
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
            decoded = str(make_header(decode_header(value)))
            try:
                decoded = decoded.encode("latin1").decode("utf-8")
            except Exception:
                pass

            return decoded
        except Exception:
            return value

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

                if (content_type == "text/plain"
                        and "attachment" not in disposition):

                    payload = part.get_payload(decode=True)

                    if payload:
                        return self._decode_payload(payload)

        else:

            payload = msg.get_payload(decode=True)

            if payload:
                return self._decode_payload(payload)

        return ""

    def _decode_payload(self, payload: bytes) -> str:
        # Tentativas mais comuns
        for enc in ("utf-8", "latin-1", "iso-8859-1", "windows-1252"):
            try:
                return payload.decode(enc)
            except Exception:
                continue

        # fallback
        return payload.decode("utf-8", errors="replace")
