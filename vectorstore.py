"""
Vector store management using ChromaDB.
Handles embeddings storage and retrieval with similarity search.
"""
import os
import shutil
from collections import defaultdict
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
    FALLBACK_TO_TOP_K_IF_BELOW_THRESHOLD,
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
        Create or load the vector store and synchronize it with the current corpus.
        """
        persist_dir = self._persist_dir()

        if force_rebuild and os.path.exists(persist_dir):
            print(f"Force rebuild: removing persisted store at {persist_dir}")
            shutil.rmtree(persist_dir)
            if os.path.exists(persist_dir):
                raise RuntimeError(f"Failed to remove persisted store: {persist_dir}")

        os.makedirs(persist_dir, exist_ok=True)
        client_settings = Settings(anonymized_telemetry=False, is_persistent=True)

        store_exists = os.path.exists(os.path.join(persist_dir, "chroma.sqlite3"))
        if store_exists:
            print(f"Loading existing vector store: {self.collection_name}")
        elif not documents:
            raise ValueError("No documents provided and no existing vector store found")

        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=persist_dir,
            client_settings=client_settings,
        )
        if documents is not None:
            stats = self._synchronize_documents(documents)
            print(
                "Index synchronization: "
                f"{stats['added']} added, {stats['removed']} removed, "
                f"{stats['unchanged']} unchanged"
            )

        print("Vector store ready!")
        return self.vectorstore

    def _synchronize_documents(self, documents: List[Document]) -> dict:
        """Synchronize current chunks by stable source path, hash, and chunk ID."""
        if not self.vectorstore:
            raise RuntimeError("Vector store not initialized")

        current_by_source: dict[str, List[Document]] = defaultdict(list)
        for document in documents:
            metadata = document.metadata
            missing = {
                key for key in ("source_path", "source_hash", "chunk_id") if not metadata.get(key)
            }
            if missing:
                raise ValueError(
                    "Document metadata is missing stable identity fields: "
                    + ", ".join(sorted(missing))
                )
            current_by_source[str(metadata["source_path"])].append(document)

        raw_existing = self.vectorstore._collection.get(include=["metadatas"])
        existing_by_source: dict[str, List[tuple[str, dict]]] = defaultdict(list)
        for existing_id, metadata in zip(
            raw_existing.get("ids", []), raw_existing.get("metadatas", [])
        ):
            metadata = metadata or {}
            source_path = str(metadata.get("source_path", ""))
            existing_by_source[source_path].append((existing_id, metadata))

        removed = 0
        added = 0
        unchanged = 0

        # Old indexes without source_path and files removed from disk are stale.
        for source_path in set(existing_by_source) - set(current_by_source):
            ids = [item[0] for item in existing_by_source[source_path]]
            if ids:
                try:
                    self.vectorstore.delete(ids=ids)
                except Exception as exc:
                    raise RuntimeError(
                        f"Failed to remove stale source {source_path!r}; "
                        "the existing index was preserved"
                    ) from exc
                removed += len(ids)

        for source_path, current_docs in current_by_source.items():
            existing_items = existing_by_source.get(source_path, [])
            existing_by_id = {item[0]: item[1] for item in existing_items}
            current_by_id = {
                str(doc.metadata["chunk_id"]): doc for doc in current_docs
            }
            existing_ids = set(existing_by_id)
            current_ids = set(current_by_id)
            existing_hashes = {
                str(metadata.get("source_hash", "")) for _, metadata in existing_items
            }
            current_hashes = {str(doc.metadata["source_hash"]) for doc in current_docs}

            if (
                existing_items
                and existing_ids == current_ids
                and existing_hashes == current_hashes
            ):
                unchanged += len(current_docs)
                continue

            overlapping_ids = existing_ids & current_ids
            conflicting_ids = {
                chunk_id
                for chunk_id in overlapping_ids
                if str(existing_by_id[chunk_id].get("source_hash", ""))
                != str(current_by_id[chunk_id].metadata["source_hash"])
            }
            if conflicting_ids:
                raise RuntimeError(
                    f"Stable chunk ID conflict for {source_path!r}; run with --rebuild"
                )

            new_ids = sorted(current_ids - existing_ids)
            stale_ids = sorted(existing_ids - current_ids)
            new_docs = [current_by_id[chunk_id] for chunk_id in new_ids]

            # Stage disjoint replacement IDs before removing the old source. If
            # embedding or persistence fails, rollback only the staged IDs and
            # leave the previous indexed source available.
            if new_ids:
                try:
                    self.vectorstore.add_documents(new_docs, ids=new_ids)
                except Exception as exc:
                    try:
                        self.vectorstore.delete(ids=new_ids)
                    except Exception as rollback_exc:
                        raise RuntimeError(
                            f"Failed to stage {source_path!r} and could not fully "
                            "rollback staged chunks; the old chunks remain indexed"
                        ) from rollback_exc
                    raise RuntimeError(
                        f"Failed to stage replacement for {source_path!r}; "
                        "the old chunks remain indexed"
                    ) from exc

            if stale_ids:
                try:
                    self.vectorstore.delete(ids=stale_ids)
                except Exception as exc:
                    raise RuntimeError(
                        f"Replacement for {source_path!r} was staged, but stale "
                        "chunk cleanup failed; new chunks remain indexed"
                    ) from exc

            added += len(new_ids)
            removed += len(stale_ids)
            unchanged += len(overlapping_ids)

        return {"added": added, "removed": removed, "unchanged": unchanged}

    def similarity_search(
        self,
        query: str,
        k: int = TOP_K,
        similarity_threshold: Optional[float] = None,
        fallback_to_top_k: Optional[bool] = None,
    ) -> List[Document]:
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
        threshold = SIMILARITY_THRESHOLD if similarity_threshold is None else similarity_threshold
        allow_fallback = (
            FALLBACK_TO_TOP_K_IF_BELOW_THRESHOLD
            if fallback_to_top_k is None
            else fallback_to_top_k
        )
        filtered_results = [doc for doc, score in results if score >= threshold]

        # If no results above threshold, return top k results anyway
        # Let LLM decide what's relevant when context is scarce
        if not filtered_results and allow_fallback:
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
            shutil.rmtree(persist_dir)
