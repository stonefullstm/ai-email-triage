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

Clone the repository:
```bash
git clone git@github.com:stonefullstm/ai-email-triage.git
cd ai-email-triage
```