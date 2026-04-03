"""
Vector store management using ChromaDB.
Handles embeddings storage and retrieval with similarity search.
"""
import os
import shutil
from typing import List, Optional, Tuple

from chromadb.config import Settings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from config import (
    EMBEDDING_MODEL,
    VECTORSTORE_DIR,
    TOP_K,
    SIMILARITY_THRESHOLD,
    GPU_DEVICE,
    DIRECTML_ADAPTER_PREFERENCE,
)


class VectorStoreManager:
    """
    Manages the vector database for document storage and retrieval.
    Uses ChromaDB with HuggingFace sentence-transformers embeddings.
    """

    def __init__(
        self,
        collection_name: str = "qa_documents",
        use_gpu: bool = False,
        gpu_device: Optional[str] = None,
    ):
        self.collection_name = collection_name
        self.use_gpu = use_gpu
        gpu_device = gpu_device or GPU_DEVICE
        device, device_label = self._resolve_embedding_device(gpu_device if use_gpu else "cpu")
        self.embedding_device = device
        self.embedding_device_label = device_label

        # Validate device
        if use_gpu:
            print(f"Configuring embeddings for device: {self.embedding_device_label}")
            print("Note: Ensure PyTorch is installed with support for this device")
            print("  - NVIDIA GPU (cuda): pip install torch --index-url https://download.pytorch.org/whl/cu118")
            print("  - Intel GPU via DirectML (recommended on Windows): pip install torch-directml")
            print("  - Mac GPU (mps): built-in with torch")
            print("  - DirectML (Windows): pip install torch-directml")

        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": device},
            encode_kwargs={"normalize_embeddings": True},
        )
        self.vectorstore: Optional[Chroma] = None

    def _resolve_embedding_device(self, requested_device: str) -> Tuple[str, str]:
        """
        Resolve user-configured device name into a torch-compatible device string.
        """
        normalized = (requested_device or "cpu").lower()

        if normalized in {"directml", "dml", "intel"}:
            try:
                import torch_directml

                count = torch_directml.device_count()
                if count == 0:
                    print("Warning: No DirectML adapters found. Falling back to CPU.")
                    return "cpu", "cpu"

                preferred = DIRECTML_ADAPTER_PREFERENCE.lower().strip()
                selected_idx = 0
                for idx in range(count):
                    name = torch_directml.device_name(idx)
                    if preferred and preferred in name.lower():
                        selected_idx = idx
                        break

                selected_name = torch_directml.device_name(selected_idx)
                resolved = str(torch_directml.device(selected_idx))
                return resolved, f"directml:{selected_idx} ({selected_name})"
            except Exception as exc:
                print(f"Warning: DirectML initialization failed ({exc}). Falling back to CPU.")
                return "cpu", "cpu"

        return normalized, normalized

    def _persist_dir(self) -> str:
        return os.path.join(VECTORSTORE_DIR, self.collection_name)

    def create_or_load(
        self,
        documents: Optional[List[Document]] = None,
        force_rebuild: bool = False,
    ) -> Chroma:
        """
        Create new vector store or load existing one.
        If documents provided and store exists, adds to it unless force_rebuild=True.
        """
        persist_dir = self._persist_dir()

        if force_rebuild and os.path.exists(persist_dir):
            print(f"Force rebuild: removing persisted store at {persist_dir}")
            shutil.rmtree(persist_dir, ignore_errors=True)

        os.makedirs(persist_dir, exist_ok=True)
        client_settings = Settings(anonymized_telemetry=False, is_persistent=True)

        if os.path.exists(os.path.join(persist_dir, "chroma.sqlite3")):
            print(f"Loading existing vector store: {self.collection_name}")
            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=persist_dir,
                client_settings=client_settings,
            )
            if documents:
                print(f"Adding {len(documents)} new documents...")
                self.vectorstore.add_documents(documents)
        else:
            if not documents:
                raise ValueError("No documents provided and no existing vector store found")
            print(f"Creating new vector store with {len(documents)} documents...")
            self.vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                collection_name=self.collection_name,
                persist_directory=persist_dir,
                client_settings=client_settings,
            )

        print("Vector store ready!")
        return self.vectorstore

    def similarity_search(self, query: str, k: int = TOP_K) -> List[Document]:
        """
        Search for similar documents to the query.
        Returns results even if below threshold to ensure we always have context.
        """
        if not self.vectorstore:
            raise RuntimeError("Vector store not initialized. Call create_or_load() first.")

        results = self.vectorstore.similarity_search_with_relevance_scores(query, k=k)

        if not results:
            return []

        # Filter by similarity threshold but always return at least the top result
        # This ensures the LLM always has some context to work with
        filtered_results = [
            doc for doc, score in results
            if score >= SIMILARITY_THRESHOLD
        ]

        # If no results above threshold, return top k results anyway
        # Let LLM decide what's relevant when context is scarce
        if not filtered_results:
            return [doc for doc, score in results]

        return filtered_results

    def get_all_documents(self) -> List[Document]:
        """
        Retrieve all documents from the vector store.
        Used for hybrid search setup.
        """
        if not self.vectorstore:
            raise RuntimeError("Vector store not initialized.")

        collection = self.vectorstore._collection
        results = collection.get(include=["documents", "metadatas"])

        documents = []
        for i, content in enumerate(results["documents"]):
            doc = Document(
                page_content=content,
                metadata=results["metadatas"][i] if i < len(results["metadatas"]) else {}
            )
            documents.append(doc)

        return documents

    def similarity_search_with_scores(
        self, query: str, k: int = TOP_K
    ) -> List[Tuple[Document, float]]:
        """
        Search with relevance scores for debugging/evaluation.
        """
        if not self.vectorstore:
            raise RuntimeError("Vector store not initialized.")

        return self.vectorstore.similarity_search_with_relevance_scores(query, k=k)

    def get_collection_stats(self) -> dict:
        """
        Get statistics about the vector store.
        """
        if not self.vectorstore:
            return {}

        collection = self.vectorstore._collection
        return {
            "document_count": collection.count(),
            "collection_name": self.collection_name,
            "embedding_model": EMBEDDING_MODEL,
        }

    def delete_collection(self):
        """
        Delete the entire collection. Use with caution!
        """
        if self.vectorstore:
            self.vectorstore.delete_collection()
            print(f"Deleted collection: {self.collection_name}")
            self.vectorstore = None

        persist_dir = self._persist_dir()
        if os.path.exists(persist_dir):
            shutil.rmtree(persist_dir, ignore_errors=True)
