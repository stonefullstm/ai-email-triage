import imaplib
import email
from email.header import decode_header, make_header


class IMAPReader:
    def __init__(self, host, username, password, mailbox="INBOX"):
        self.host = host
        self.username = username
        self.password = password
        self.mailbox = mailbox
        self.conn = None

    def connect(self):
        self.conn = imaplib.IMAP4_SSL(self.host)
        self.conn.login(self.username, self.password)
        self.conn.select(self.mailbox)

    def fetch_unseen(self):
        status, messages = self.conn.search(None, "UNSEEN")
        ids = messages[0].split()

        emails = []

        for mail_id in ids:
            status, msg_data = self.conn.fetch(mail_id, "(RFC822)")
            raw_email = msg_data[0][1]

            msg = email.message_from_bytes(raw_email)

            emails.append(self._parse_email(msg))

        return emails

    def _parse_email(self, msg):
        raw_subject = msg["Subject"]
        if raw_subject:
            subject = str(make_header(decode_header(raw_subject)))
        else:
            subject = ""

        sender = msg.get("From")
        body = self._get_body(msg)

        return {"subject": subject, "sender": sender, "body": body}

    def _get_body(self, msg):
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    return part.get_payload(decode=True).decode()
        else:
            return msg.get_payload(decode=True).decode()

        return ""
