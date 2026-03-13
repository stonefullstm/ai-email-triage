# Contributing to ai-triage

Thank you for your interest in contributing! This project is a local, privacy-first CLI tool for AI-powered email triage. Contributions are welcome — whether fixing bugs, improving the pipeline, adding tests, or improving documentation.

---

## Table of Contents

- [Contributing to ai-triage](#contributing-to-ai-triage)
  - [Table of Contents](#table-of-contents)
  - [Project Overview](#project-overview)
  - [Getting Started](#getting-started)
  - [Project Structure](#project-structure)
  - [Development Workflow](#development-workflow)
  - [Running Tests](#running-tests)
    - [Isolation rules](#isolation-rules)
    - [Example of a correct fixture:](#example-of-a-correct-fixture)
  - [Code Style](#code-style)
  - [Opening a Pull Request](#opening-a-pull-request)
  - [Questions?](#questions)

---

## Project Overview

`ai-triage` classifies emails through a layered pipeline — each layer is faster and cheaper than the next:

Hash Cache → Embedding Similarity → Heuristic Rules → LLM (fallback)


Labels, heuristics, and model settings are fully configurable via `triage.yaml` and `.env` — no hardcoded values.

---

## Getting Started

```bash
git clone https://github.com/your-username/ai-triage.git
cd ai-triage

python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

pip install -e ".[dev]"

cp .env.example .env            # fill in your credentials
cp triage.yaml.example triage.yaml  # define your labels

Gmail users: use an App Password, not your account password.
```
---

## Project Structure

```text
triage/
├── cli/           # CLI interface (Typer)
│
├── config/        # Application configuration
│   ├── app_config.py
│   └── rules.yaml
│
├── core/          # Classification engine
│   ├── pipeline.py
│   ├── heuristics.py
│   ├── embedding.py
│   ├── llm_fallback.py
│   ├── hash_cache.py
│   └── rules_loader.py
│
├── data/          # Persistent storage
│   ├── classification_store.py
│   ├── embedding_store.py
│   └── processed_store.py
│
├── email/         # Email ingestion and parsing
│   ├── imap_reader.py
│   ├── parser.py
│   └── models.py
│
├── embedder/      # Sentence-transformer wrapper
│   └── model.py
│
├── llm/           # LLM integration
│   └── ollama_client.py
│
├── tools/         # Utility scripts
│   └── export_eml.py
│
└── examples/      # Sample emails for testing
```
---
## Development Workflow

```bash
# run the pipeline in dry-run mode (no DB writes)
triage run --dry-run

# interactive annotation (adds examples to embedding store)
triage review

# check classification metrics
triage stats
```
---
## Running Tests

The test suite uses pytest. All tests must be fully isolated — no test should touch the real database.
```bash
pytest                  # run all tests
pytest -v               # verbose
pytest tests/unit/      # only unit tests
pytest --tb=short       # shorter tracebacks
```
### Isolation rules
- Always use tmp_path fixtures for any EmbeddingStore, ProcessedStore, or StatsStore instantiation in tests.

- Use MagicMock for encoders — never load a real SentenceTransformer model in unit tests.

- Never import from triage.config in tests without mocking — it reads .env and triage.yaml from disk.

### Example of a correct fixture:
```python
@pytest.fixture
def embedding_store(tmp_path):
    return EmbeddingStore(db_path=tmp_path / "test.db")

@pytest.fixture
def layer(similar_encoder, embedding_store):
    return EmbeddingLayer(encoder=similar_encoder, store=embedding_store)
```
---
## Code Style
- Formatter: ruff format

- Linter: ruff check

- Type hints: required on all public methods

- Docstrings: English, brief, on public classes and methods

---

## Opening a Pull Request
1. Fork the repository and create a branch: git checkout -b feat/your-feature

2. Make your changes with tests

3. Run ruff and pytest — both must pass cleanly

4. Open a PR with a clear description of what changed and why

5. Link any related issue

---

## Questions?

Open an issue or start a discussion. Contributions of any size are welcome.

