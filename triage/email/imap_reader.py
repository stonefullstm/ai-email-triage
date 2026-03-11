import imaplib
from datetime import datetime, timedelta


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

    def fetch_unseen(self, days: int = 1, limit: int = 10):
        since = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
        status, messages = self.conn.search(None, f'(UNSEEN SINCE {since})')
        ids = messages[0].split()[-limit:]

        raw_emails = []

        for i, mail_id in enumerate(ids):
            # print(f"  → Processing {i+1}/{len(ids)}...", flush=True)
            status, msg_data = self.conn.fetch(mail_id, "(BODY.PEEK[])")
            raw_email = msg_data[0][1]

            raw_emails.append(raw_email)

        return raw_emails
