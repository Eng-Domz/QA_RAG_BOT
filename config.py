"""
Configuration settings for the QA Bot.
Centralizing config makes it easy to tune without touching business logic.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Disable Chroma anonymized telemetry to avoid noisy runtime telemetry errors.
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCUMENTS_DIR = os.path.join(BASE_DIR, "documents")
VECTORSTORE_DIR = os.path.join(BASE_DIR, "chroma_db")

# Create directories if they don't exist
os.makedirs(DOCUMENTS_DIR, exist_ok=True)
os.makedirs(VECTORSTORE_DIR, exist_ok=True)

# Embedding Configuration
# MiniLM is fast and good quality. For better quality use 'all-mpnet-base-v2'
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
USE_GPU = os.getenv("USE_GPU", "false").lower() == "true"
GPU_DEVICE = os.getenv("GPU_DEVICE", "cuda")  # Options: cuda, directml, xpu, mps
DIRECTML_ADAPTER_PREFERENCE = os.getenv("DIRECTML_ADAPTER_PREFERENCE", "intel")

# Text Splitting Configuration
# Best practice: Smaller chunks (500-1000) with overlap work better for retrieval
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))

# Retrieval Configuration
TOP_K = int(os.getenv("TOP_K", "5"))  # Number of chunks to retrieve
SIMILARITY_THRESHOLD = 0.3  # Minimum similarity score (0-1)

# LLM Configuration
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
LLM_TEMPERATURE = 0.3  # Lower = more factual, Higher = more creative
MAX_TOKENS = 1000

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Ollama (local models) - FREE, no API key needed!
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")  # or "llama2", "mistral"
