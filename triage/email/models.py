from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class EmailMessage:
    subject: str
    sender: str
    to: Optional[str]
    date: Optional[datetime]
    body: str
