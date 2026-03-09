![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

# AI E-mail Triage

AI-powered email triage system that automatically classifies and prioritizes incoming emails using a hybrid approach combining heuristics, semantic embeddings, and LLM-based classification.

The goal of this project is to reduce the need for expensive LLM calls by resolving most classifications using fast local logic.

---

## Overview

Managing email inboxes efficiently is difficult when messages include support requests, partnership proposals, automated notifications, and general communication.

This project implements a **multi-stage classification pipeline** that progressively applies:

1. Heuristics (rules and keyword signals)
2. Semantic similarity using embeddings
3. Scoring and confidence evaluation
4. LLM fallback when the system is uncertain

This architecture allows most emails to be classified **locally and quickly**, with LLM usage only when necessary.

---

## Architecture

The system follows a modular pipeline:

```
IMAP → Email Parser → Heuristics → Embeddings → Scoring → LLM (fallback)
```

### Modules

```
triage/
│
├── core
│   ├── engine.py        # classification pipeline
│   ├── heuristics.py    # rule-based signals
│   ├── scoring.py       # confidence evaluation
│   └── categories.py    # category definitions
│
├── email
│   └── imap_reader.py   # IMAP email ingestion
│
├── embeddings
│   └── model.py         # semantic embedding model
│
└── llm
    └── classifier.py    # LLM-based fallback classifier
```

---

## How It Works

### 1. Email ingestion

Emails are fetched from an IMAP server.

### 2. Parsing

The system extracts:

* subject
* sender
* message body

### 3. Heuristic signals

Fast rule-based checks detect common patterns such as:

* partnership requests
* automated notifications
* marketing emails

### 4. Semantic similarity

If heuristics are inconclusive, the system generates embeddings and compares the message against category examples.

### 5. Scoring

Signals from heuristics and embeddings are combined to produce a confidence score.

### 6. LLM fallback

If confidence is too low, the message is sent to an LLM classifier.

---

## Installation

Clone the repository:

```bash
git clone git@github.com:stonefullstm/ai-email-triage.git
cd ai-email-triage
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Example Usage

Example workflow:

```python
from triage.core.engine import TriageEngine
from triage.email.imap_reader import IMAPReader

reader = IMAPReader(host, username, password)
reader.connect()

emails = reader.fetch_unseen()

engine = TriageEngine()

for email in emails:
    result = engine.classify(email)
    print(result.category)
```

---

## Project Status

🚧 **Work in progress**

Current focus:

* email ingestion
* rule-based classification
* semantic similarity
* scoring engine

---

## Roadmap

Planned improvements:

* [ ] Email parser improvements
* [ ] Embedding-based similarity search
* [ ] Configurable rule system
* [ ] CLI interface
* [ ] Gmail API integration
* [ ] Web dashboard

---

## Design Goals

* Minimize LLM usage
* Fast local classification
* Modular architecture
* Easy to extend with new categories
* Provider-agnostic LLM integration

---

## Contributing

Contributions are welcome.

Feel free to open issues, suggest improvements, or submit pull requests.

---

## License

MIT License
