![Python](https://img.shields.io/badge/python-3.12+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

# AI Triage

AI Triage is an open-source tool that classifies emails using a layered AI pipeline designed to be fast, explainable, and cost-efficient.

Instead of sending every email to a large language model, AI Triage uses a cascading architecture:
```text
hash cache → heuristics → embeddings → LLM fallback
```
Cheap and deterministic methods are used first. The LLM is only invoked when necessary.

This makes the system:

- ⚡ fast

- 💸 low-cost

- 🔍 explainable

- 🔒 privacy-friendly
---

## Architecture

The classification engine is built as a modular pipeline where each stage is responsible for a specific type of analysis.

```text
Email
  │
  ▼
HashCacheLayer
  │
  ▼
HeuristicLayer
  │
  ▼
EmbeddingLayer
  │
  ▼
LLMFallbackLayer
  │
  ▼
ClassificationResult
```
### Pipeline Stages

#### Hash Cache

- Avoids reprocessing the same email

- Uses content hash for deduplication

#### Heuristics

- Regex patterns

- Sender matching

- Fast deterministic rules defined in rules.yaml

#### Embeddings

- Semantic similarity using sentence-transformers

- Compares email vectors against labeled examples

- Majority vote classification

#### LLM Fallback

- Final fallback when confidence is low

- Uses an LLM through Ollama

- Returns structured JSON output
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
## Installation

### Clone the repository:
```bash
git clone git@github.com:stonefullstm/ai-email-triage.git
cd ai-email-triage
```
### Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate
```
### Install the project:
```bash
pip install -e .
```
---
## Running the CLI

The CLI is built using Typer.

### Classify emails
```bash
triage run
```
This connects to IMAP and classifies last e-mails
```text
⏳ Connecting to IMAP...
⏳ Searching for e-mails (last 1 day(s), limit 10)...
📬 10 e-mail(s) found.

Batches: 100%|█████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 21.43it/s]
[HEURISTIC] 'Everyone gets more orgs and invites, Webhooks + Org settings' → FYI_IGNORE (95%)
Batches: 100%|█████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 24.82it/s]
[HEURISTIC] 'Try these common ways to use Perplexity' → FYI_IGNORE (95%)
Batches: 100%|████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 116.88it/s]
2026-03-13 22:04:42,546 [INFO] httpx - HTTP Request: POST http://127.0.0.1:11434/api/chat "HTTP/1.1 200 OK"
[LLM] '🚨 Mega Promo LATAM ✈️ Voos a partir de 10x R$25 SEM JUROS!' → ACTION_REQUIRED (95%)
Batches: 100%|█████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 20.12it/s]
2026-03-13 22:04:59,915 [INFO] httpx - HTTP Request: POST http://127.0.0.1:11434/api/chat "HTTP/1.1 200 OK"
[LLM] 'Ofertas 🤝 Segurança' → FYI_IGNORE (95%)
```

### Run the demo
```bash
triage demo examples/bank_invoice.eml
```
This runs several example emails located in the examples/ directory.
```text
📧 Processing: bank_invoice.eml
  📧 Sender: Nubank <noreply@nubank.com.br>
  📋 Subject: Fatura de março disponível
  📝 Body (first lines):
    Olá Carlos,
    
    Sua fatura de março já está disponível para pagamento.

Batches: 100%|█████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 22.77it/s]
[HEURISTIC] → REFERENCE_ONLY (88%)
```
---
## Data Storage

AI Triage uses SQLite for persistence.

Tables include:

- processed emails

- classification history

- embedding vectors

This allows:

- incremental learning

- reproducible experiments

- offline operation
---
## Example Emails

The repository includes sample .eml files in:
```text
triage/examples/
```

These are useful for testing and demonstrations.

---

## Roadmap

Potential future improvements:

- Gmail API integration

- IMAP batch processing

- active learning from user feedback

- vector database support

- web dashboard

- automated dataset evaluation
---
## Contributing

Contributions are welcome.

You can help by:

- improving heuristics

- adding embedding datasets

- writing tests

- improving documentation

See CONTRIBUTING.md for details.

---
## License

This project is licensed under the MIT License.