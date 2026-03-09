import email
from email.header import decode_header
from email.utils import parsedate_to_datetime

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

        decoded_parts = decode_header(value)

        parts = []

        for part, encoding in decoded_parts:

            if isinstance(part, bytes):
                parts.append(part.decode(encoding or "utf-8", errors="ignore"))
            else:
                parts.append(part)

        return "".join(parts)

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

                if (
                    content_type == "text/plain"
                    and "attachment" not in disposition
                ):

                    payload = part.get_payload(decode=True)

                    if payload:
                        return payload.decode(
                            errors="ignore"
                        )

        else:

            payload = msg.get_payload(decode=True)

            if payload:
                return payload.decode(errors="ignore")

        return ""
