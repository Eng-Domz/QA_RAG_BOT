# QA RAG Bot

An independently designed retrieval-augmented generation learning system for
querying lecture materials with local or hosted language models. The project
explores persistent vector search, source attribution, grounding controls,
hybrid retrieval, query expansion, HyDE, and provider-backed evaluation.

The current release is a local command-line application being hardened toward
a production-grade bilingual knowledge platform. See [Current limitations](#current-limitations)
for the features it does not yet claim to provide.

## What it demonstrates

- Loading PDF, TXT, Markdown, and DOCX documents.
- Repeatable chunking with stable source paths, file hashes, and chunk IDs.
- Idempotent synchronization of added, changed, unchanged, and deleted sources.
- Semantic retrieval with normalized Hugging Face embeddings and Chroma.
- Optional BM25 plus semantic hybrid retrieval.
- Local generation with Ollama or hosted generation with OpenAI.
- Optional strict grounding, query expansion, HyDE, and source attribution.
- Deterministic automated tests that do not need a model or API key.
- A separate provider-backed manual evaluation command.

## Architecture

```text
documents/
    |
    v
DocumentProcessor ----> stable source and chunk identity
    |
    v
VectorStoreManager ---> Chroma synchronization and semantic search
    |                              |
    |                              +--> optional BM25 hybrid ranking
    v
QABot -------------> grounding gate -> prompt -> Ollama/OpenAI
    |
    +--> answer, context summary, and source metadata
```

Key modules:

- `config.py`: validated environment configuration.
- `document_loader.py`: loading, metadata, hashing, and chunking.
- `vectorstore.py`: persistent Chroma synchronization and retrieval.
- `advanced_rag.py`: hybrid retrieval, query expansion, and HyDE.
- `qa_chain.py`: retrieval orchestration, grounding, and generation.
- `main.py`: local interactive CLI.
- `run_tests.py`: manual provider-backed evaluation, not the automated test suite.
- `tests/`: deterministic unit tests.

## Requirements

- Python 3.11.
- Git.
- For local generation: [Ollama](https://ollama.com/) and the configured model.
- For hosted generation: an OpenAI API key.

Python 3.14 is not supported by the pinned LangChain/Chroma generation used by
this release.

## Quick start with Ollama

```powershell
git clone https://github.com/Eng-Domz/QA_RAG_BOT.git
cd QA_RAG_BOT

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Copy-Item .env.example .env
ollama pull llama3.2:1b
python setup.py
python main.py --rebuild
```

On macOS or Linux, activate the environment with:

```bash
source .venv/bin/activate
```

Add your own supported files below `documents/` before rebuilding the index.

## Configuration

Copy `.env.example` to `.env`. Configuration is validated at startup; invalid
booleans, ranges, modes, weights, or chunk settings fail with a clear message.

Important settings:

| Variable | Default | Purpose |
|---|---:|---|
| `LLM_PROVIDER` | `ollama` | `ollama` or `openai` |
| `OLLAMA_MODEL` | `llama3.2:1b` | Local generation model |
| `LLM_MODEL` | `gpt-4o-mini` | Hosted OpenAI model |
| `LLM_TEMPERATURE` | `0.3` | Generation temperature from 0 to 2 |
| `MAX_TOKENS` | `1000` | Maximum hosted-model output tokens |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model |
| `CHUNK_SIZE` | `1000` | Characters per chunk |
| `CHUNK_OVERLAP` | `200` | Overlap; must be smaller than chunk size |
| `TOP_K` | `5` | Maximum retrieved chunks |
| `SIMILARITY_THRESHOLD` | `0.3` | Minimum semantic relevance in the 0–1 range |
| `RETRIEVAL_MODE` | `standard` | `standard` or `hybrid` |
| `STRICT_GROUNDING` | `false` | Refuse when semantic evidence is insufficient |
| `FALLBACK_TO_TOP_K_IF_BELOW_THRESHOLD` | `true` | Allow weak context outside strict mode |

The complete documented configuration lives in `.env.example`.

## Privacy and provider choice

Ollama runs generation locally, so document context stays on the machine unless
another component is configured to transmit it.

When `LLM_PROVIDER=openai`, the question and retrieved document excerpts are
sent to OpenAI for generation. Do not use hosted generation for private,
regulated, employer-owned, or confidential documents without authorization and
an appropriate data-handling agreement.

## Index lifecycle

Each source records a normalized relative path and SHA-256 content hash. Each
chunk receives a deterministic ID. On startup the index is synchronized:

- unchanged sources are skipped;
- changed sources replace their old chunks;
- new sources are added;
- sources removed from `documents/` are removed from the index.

If every source has intentionally been removed, clear the remaining persisted
chunks without starting the QA session:

```powershell
python main.py --sync-empty
```

The stable metadata schema differs from older releases. Run this once after
upgrading:

```powershell
python main.py --rebuild
```

Rebuilding removes only the generated collection below `chroma_db/`; original
documents are not modified.

## Retrieval and grounding

Standard mode uses semantic similarity. Hybrid mode combines semantic search
with BM25 keyword search and requires `rank-bm25`, which is included in
`requirements.txt`.

Strict mode refuses when no semantic result meets the configured threshold:

```env
STRICT_GROUNDING=true
SIMILARITY_THRESHOLD=0.35
FALLBACK_TO_TOP_K_IF_BELOW_THRESHOLD=false
```

Hybrid rankings do not pretend that BM25 and vector scores share one scale.
Instead, strict hybrid mode requires a semantic relevance gate before accepting
the hybrid ranking.

## Interactive usage

```powershell
python main.py
```

Commands:

- `/sources`: toggle source paths.
- `/debug`: inspect semantic retrieval scores.
- `/quit`: exit.

Use `--rebuild` only when you intentionally want a clean index.

## Automated tests

The automated suite mocks external providers and storage boundaries. It does
not require Ollama, API credentials, or an embedding-model download.

```powershell
python -m pip install -r requirements-dev.txt
python -m pip check
python -m compileall -q .
python -m pytest -q
```

CI runs these commands on Python 3.11 for pushes to `main` and pull requests.

## Manual evaluation

`run_tests.py` is a provider-backed manual evaluation command, despite its
historical name. It rebuilds the local index, sends the questions in
`test_questions.txt` to Ollama, and writes successes and failures separately.
It exits non-zero if any question fails.

```powershell
python run_tests.py --output test_results.local.json
python run_tests.py --rate --output test_results.rated.local.json
```

Manual ratings are not a reproducible quality metric. The roadmap includes a
bilingual dataset with retrieval hit rate, citation correctness, grounded
refusal, latency, and cost measurements.

## GPU configuration

CPU is the verified default. GPU support depends on a compatible PyTorch build:

```env
USE_GPU=true
GPU_DEVICE=cuda
```

Windows DirectML and Apple MPS may be selected with `directml` and `mps`.
Hardware-specific installations are intentionally not forced by the base
requirements.

## Current limitations

- Local CLI only; no web API, multi-user authentication, or hosted deployment.
- No production rate limiting, audit log, monitoring, or service health check.
- The checked-in question file is a manual study set, not a measured bilingual benchmark.
- Provider-backed end-to-end evaluation requires a separately installed model or API access.
- The dependency generation is deliberately pinned for reproducibility and should
  be upgraded in a separate compatibility change.
- Strict grounding reduces unsupported answers but does not prove factual correctness.

## Roadmap

1. Publish a reproducible Arabic/English retrieval and grounding baseline.
2. Add a backend API with validation, health endpoints, and structured logging.
3. Add PostgreSQL/pgvector document and conversation persistence.
4. Build an accessible bilingual web interface with RTL/LTR support.
5. Add deployment, observability, security review, and operational documentation.

## License

Licensed under the [MIT License](LICENSE).

## Author

Built by [Adham Ahmed](https://github.com/Eng-Domz) as an independent project
for learning from lecture materials and developing practical RAG engineering
skills.
