import imaplib


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

        raw_emails = []

        for mail_id in ids:
            status, msg_data = self.conn.fetch(mail_id, "(RFC822)")
            raw_email = msg_data[0][1]

            raw_emails.append(self._parse_email(raw_email))

        return raw_emails
