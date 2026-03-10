import hashlib
import imaplib
import email
from email.utils import parsedate_to_datetime
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()


def export_eml(
    host=os.environ["IMAP_SERVER"],
    username=os.environ["MAIL_ACCOUNT"],
    password=os.environ["EMAIL_PASSWORD"],
    mailbox: str = "INBOX",
    limit: int = 10,
    output_dir: str = "triage/examples",
):
    """
    Export raw IMAP messages as .eml files
    """

    Path(output_dir).mkdir(exist_ok=True)

    print(f"📡 Connecting to IMAP server {host}...")
    conn = imaplib.IMAP4_SSL(host)
    conn.login(username, password)
    conn.select(mailbox)

    print("🔍 Searching for emails...")
    status, messages = conn.search(None, "ALL")
    ids = messages[0].split()

    # Get the most recent
    ids = ids[-limit:]

    for i, mail_id in enumerate(ids, 1):
        status, msg_data = conn.fetch(mail_id, "(RFC822)")

        raw = msg_data[0][1]  # bytes of entire email
        msg = email.message_from_bytes(raw)

        # Create filename based on date and time
        msg_date = msg.get("Date", f"email_{i}")
        msg_date = parsedate_to_datetime(msg_date).isoformat()
        hash_date = hashlib.sha256(msg_date.encode('utf-8')).hexdigest()
        filename = Path(output_dir) / f"{hash_date}.eml"
        filename.write_bytes(raw)

        print(f"📨 Saved: {filename.name}")

    print("✨ Done.")


def _sanitize_filename(text: str) -> str:
    """
    Remove forbidden characters in filenames.
    """
    invalid = '<>:"/\\|?*'
    for ch in invalid:
        text = text.replace(ch, "_")

    # Limit length
    return text[:80].strip() or "email"


if __name__ == "__main__":
    export_eml()
