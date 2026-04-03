# Advanced RAG Question Answering System

A production-ready Question Answering system using **Retrieval-Augmented Generation (RAG)** architecture. Built with LangChain, ChromaDB, and supporting both OpenAI and local Ollama LLMs.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![LLM](https://img.shields.io/badge/LLM-OpenAI%20%7C%20Ollama-orange)

---

## Table of Contents

- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Advanced Features](#advanced-features)
- [GPU Acceleration](#gpu-acceleration)
- [Testing & Evaluation](#testing--evaluation)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)
- [License](#license)

---

## Features

- **Multi-Format Document Support** - PDF, TXT, Markdown, Word documents
- **Hybrid Search** - Combine semantic (vector) + lexical (BM25) retrieval
- **Flexible LLM Options** - OpenAI (cloud) or Ollama (local, free)
- **GPU Acceleration** - CUDA, DirectML, MPS support for embedding generation
- **Query Expansion** - Automatic query rephrasing for better retrieval
- **HyDE** - Hypothetical Document Embeddings for improved accuracy
- **Source Attribution** - Track which documents contributed to answers
- **Debug Mode** - Inspect retrieved documents and relevance scores
- **Batch Processing** - Evaluate multiple questions and export results

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        RAG Pipeline                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │ Documents│───▶│  Chunk   │───▶│ Embedding│───▶│ Vector   │  │
│  │  (PDF,   │    │ Splitter │    │  Model   │    │  Store   │  │
│  │  TXT)    │    │          │    │          │    │ (Chroma) │  │
│  └──────────┘    └──────────┘    └──────────┘    └────┬─────┘  │
│                                                       │        │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐         │        │
│  │  Answer  │◀───│   LLM    │◀───│  Context │◀────────┘        │
│  │          │    │(OpenAI/  │    │Retrieval │                  │
│  │          │    │ Ollama)  │    │          │                  │
│  └──────────┘    └──────────┘    └──────────┘                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# 1. Clone and setup
git clone <your-repo-url>
cd claude_proj_1
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure (Ollama - no API key needed)
copy .env.example .env  # Windows
cp .env.example .env    # Mac/Linux

# 4. Add documents to ./documents folder

# 5. Run
python main.py
```

---

## Installation

### Prerequisites

- Python 3.9 or higher
- pip package manager
- Git (for cloning)

### Step 1: Clone Repository

```bash
git clone <your-repo-url>
cd claude_proj_1
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Optional - Setup Ollama (Free Local LLM)

```bash
# Download from https://ollama.ai
# Then pull a model:
ollama pull llama3.2:1b
```

### Step 5: Verify Installation

```bash
python setup.py
```

---

## Configuration

Copy the example environment file and customize:

```bash
cp .env.example .env
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | `openai` or `ollama` |
| `OPENAI_API_KEY` | - | Your OpenAI API key (required if using OpenAI) |
| `LLM_MODEL` | `gpt-3.5-turbo` | OpenAI model name |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2:1b` | Ollama model name |
| `LLM_TEMPERATURE` | `0.3` | 0.0 (factual) to 1.0 (creative) |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | HuggingFace embedding model |
| `USE_GPU` | `false` | Enable GPU acceleration |
| `GPU_DEVICE` | `directml` | `cuda`, `directml`, `xpu`, or `mps` |
| `CHUNK_SIZE` | `1000` | Characters per chunk |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `TOP_K` | `5` | Number of documents to retrieve |

---

## Usage

### Interactive Mode

```bash
python main.py
```

**Commands:**
- Ask natural language questions
- `/quit` or `/q` - Exit
- `/debug` - Show retrieved documents with scores
- `/sources` - Toggle source display

### Rebuild Vector Store

```bash
python main.py --rebuild
```

### Programmatic Usage

```python
from document_loader import DocumentProcessor
from vectorstore import VectorStoreManager
from qa_chain import QABot

# Process documents
processor = DocumentProcessor()
docs = processor.process("./documents")

# Create vector store
store = VectorStoreManager()
store.create_or_load(docs)

# Initialize bot
bot = QABot(store, use_openai=False, use_ollama=True)
bot.initialize_chain()

# Ask questions
result = bot.ask("What is deep learning?")
print(result["answer"])
print(f"Sources: {result['sources']}")
```

### Batch Processing

```python
from batch_processor import BatchProcessor

questions = [
    "What is machine learning?",
    "How does backpropagation work?",
    "What are transformers?",
]

batch = BatchProcessor(bot)
results = batch.process_questions(questions, save_path="results.json")
```

---

## Project Structure

```
claude_proj_1/
├── config.py              # Centralized configuration
├── document_loader.py     # Document loading and chunking
├── vectorstore.py         # ChromaDB vector store management
├── qa_chain.py            # RAG chain and LLM integration
├── advanced_rag.py        # Hybrid search, query expansion, HyDE
├── batch_processor.py     # Batch question processing
├── main.py                # Entry point and CLI
├── setup.py               # Setup validation script
├── requirements.txt       # Python dependencies
├── .env                   # Environment configuration
├── .env.example           # Example configuration
├── documents/             # Place your documents here
│   ├── sample_document.txt
│   └── deep_learning_lecture.txt
├── chroma_db/             # Vector store (auto-created)
└── Explanation/           # Detailed documentation
```

---

## How It Works

### 1. Document Ingestion

Documents are loaded from the `./documents` folder and processed:
- **Load**: PDF, TXT, MD, DOCX files
- **Split**: Recursive character splitting with semantic boundaries
- **Embed**: Convert to vectors using HuggingFace models
- **Store**: Save in ChromaDB with metadata

### 2. Retrieval

When you ask a question:
1. Question is embedded using the same model
2. Similar documents are found via cosine similarity
3. Top-K results are returned (filtered by threshold)

### 3. Answer Generation

The retrieved context + question are sent to the LLM:
```
Context: [retrieved document chunks]
Question: [user question]
Answer: [LLM generates response based on context]
```

### 4. RAG Prompt Template

```
You are a helpful AI assistant answering questions based on the provided context.

Instructions:
1. Use the context below as your PRIMARY source of information
2. Answer based on the context when possible
3. If context doesn't have enough info, say so but still try to help
4. Be concise, specific, and practical
5. Mention the source file when answering from context

Context: {context}
Question: {question}
Answer:
```

---

## Advanced Features

### Hybrid Search (BM25 + Semantic)

Combine keyword matching with semantic understanding:

```python
from advanced_rag import AdvancedRetriever

retriever = AdvancedRetriever(vectorstore_manager)
retriever.setup_hybrid_search(weights=[0.5, 0.5])  # [semantic, bm25]
docs = retriever.retrieve("your query", method="hybrid")
```

**Best for:** Technical terms, product codes, exact match requirements

### Query Expansion

Generate multiple query variants for better coverage:

```python
from advanced_rag import QueryExpansion

variants = QueryExpansion.generate_variants("what is ML?", llm)
# Returns: ["what is ML?", "define machine learning", "explain ML"]
```

**Best for:** Vocabulary mismatch, improving recall

### HyDE (Hypothetical Document Embeddings)

Generate a hypothetical answer, then search for similar content:

```python
hypothetical = QueryExpansion.hyde_generate("what is overfitting?", llm)
# Generates: "Overfitting occurs when a model learns training data too well..."
# Then searches for documents similar to this hypothetical answer
```

**Best for:** Questions structurally different from document content

---

## GPU Acceleration

### NVIDIA GPUs (CUDA)

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

```env
USE_GPU=true
GPU_DEVICE=cuda
```

### Intel GPUs (DirectML - Windows)

```bash
pip install torch-directml
```

```env
USE_GPU=true
GPU_DEVICE=directml
DIRECTML_ADAPTER_PREFERENCE=intel
```

### Mac GPUsMPS

```env
USE_GPU=true
GPU_DEVICE=mps
```

---

## Testing & Evaluation

### Run Test Questions

```bash
# Load questions from file
python -c "
from main import ingest_documents, QABot
from batch_processor import BatchProcessor

store = ingest_documents()
bot = QABot(store, use_ollama=True)
bot.initialize_chain()

with open('test_questions.txt') as f:
    questions = [l.strip() for l in f if l.strip() and not l.startswith('#')]

batch = BatchProcessor(bot)
results = batch.process_questions(questions, save_path='test_results.json')
"
```

### Evaluation Metrics

Rate outputs on:
1. **Relevance** - Does the answer address the question?
2. **Accuracy** - Is the information correct?
3. **Completeness** - Does it cover all aspects?
4. **Source Quality** - Are retrieved documents relevant?

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `No module named X` | Run `pip install -r requirements.txt` |
| `API key error` | Set `OPENAI_API_KEY` or use Ollama |
| `No documents found` | Add files to `documents/` folder |
| `Ollama connection failed` | Ensure Ollama is running: `ollama serve` |
| Wrong/hallucinated answers | Check retrieved docs with `/debug`, adjust `TOP_K` or `CHUNK_SIZE` |
| Slow responses | Use smaller model, reduce `TOP_K`, enable GPU |
| GPU not working | Verify PyTorch installation: `python -c "import torch; print(torch.cuda.is_available())"` |

---

## Best Practices

### Chunking Strategy
- **500-800 chars** for specific facts/QA
- **1000-1500 chars** for general understanding
- **20% overlap** preserves context across boundaries

### Embedding Models
| Model | Use Case |
|-------|----------|
| `all-MiniLM-L6-v2` | Fast, good quality (default) |
| `all-mpnet-base-v2` | Better quality, slower |
| `multi-qa-mpnet-base-dot-v1` | Optimized for QA tasks |

### Retrieval Tuning
- Start with `TOP_K=5`
- Increase for complex questions
- Adjust `SIMILARITY_THRESHOLD` based on results

### Prompt Engineering
- Be specific in questions
- Include context hints
- Use domain-specific terminology

---

## License

MIT License - Free to use and modify.

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

---

## Acknowledgments

- [LangChain](https://python.langchain.com/) - RAG orchestration framework
- [ChromaDB](https://docs.trychroma.com/) - Vector database
- [HuggingFace](https://huggingface.co/) - Embedding models
- [Ollama](https://ollama.ai/) - Local LLM runtime
