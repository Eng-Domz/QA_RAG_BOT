"""
Advanced RAG techniques for better performance.
Includes re-ranking and hybrid search options.
"""
from typing import List
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever

# EnsembleRetriever moved between packages across LangChain versions.
try:
    from langchain.retrievers import EnsembleRetriever
except ImportError:
    from langchain_community.retrievers import EnsembleRetriever

from vectorstore import VectorStoreManager
from config import TOP_K


class AdvancedRetriever:
    """
    Advanced retrieval techniques for better results.
    """

    def __init__(self, vectorstore_manager: VectorStoreManager):
        self.vectorstore_manager = vectorstore_manager
        self.bm25_retriever = None
        self.ensemble_retriever = None

    def setup_hybrid_search(self, documents: List[Document] = None, weights: List[float] = None):
        """
        Combine semantic (vector) + lexical (BM25) search.

        Best for: When you need both semantic understanding AND keyword matching.
        Example: Product codes, technical terms that need exact matches.

        Args:
            documents: Optional list of documents. If None, retrieves from vectorstore.
            weights: [semantic_weight, bm25_weight] - defaults to [0.5, 0.5]
        """
        if weights is None:
            weights = [0.5, 0.5]

        # Get documents if not provided
        if documents is None:
            documents = self.vectorstore_manager.get_all_documents()

        if not documents:
            print("Warning: No documents available for hybrid search setup")
            return self

        # BM25 (keyword-based)
        self.bm25_retriever = BM25Retriever.from_documents(documents)
        self.bm25_retriever.k = TOP_K

        # Vector store retriever
        vector_retriever = self.vectorstore_manager.vectorstore.as_retriever(
            search_kwargs={"k": TOP_K}
        )

        # Ensemble combines both
        self.ensemble_retriever = EnsembleRetriever(
            retrievers=[vector_retriever, self.bm25_retriever],
            weights=weights,
        )

        print("Hybrid search (BM25 + Semantic) configured")
        return self

    def retrieve(self, query: str, method: str = "standard", k: int = TOP_K) -> List[Document]:
        """
        Retrieve documents using the specified method.

        Args:
            query: The search query
            method: "standard" or "hybrid"
        """
        if method == "hybrid" and self.ensemble_retriever:
            docs = self.ensemble_retriever.invoke(query)
            return docs[:k]
        else:
            return self.vectorstore_manager.similarity_search(query, k=k)


class QueryExpansion:
    """
    Query expansion techniques for better retrieval.
    """

    @staticmethod
    def generate_variants(query: str, llm=None) -> List[str]:
        """
        Generate query variants using LLM.

        Best for: When the original query might not match document vocabulary.
        """
        if llm is None:
            # Simple variants without LLM
            variants = [
                query,
                query.lower(),
                query.replace("what is", "").strip(),
            ]
            return list(set(variants))

        # With LLM - generate rephrasings
        prompt = f"""Generate 3 different ways to ask this question. Return only the questions, one per line, numbered:
Question: {query}

1."""

        try:
            response = llm.invoke(prompt)
            if hasattr(response, 'content'):
                response = response.content
            # Parse response - extract numbered variants
            variants = [query]  # Always include original
            for line in response.split("\n"):
                line = line.strip()
                # Remove numbering like "1.", "2.", etc.
                if line and line[0].isdigit() and "." in line:
                    line = line.split(".", 1)[1].strip()
                if line and len(line) > 5:  # Avoid very short fragments
                    variants.append(line)
            # Preserve order while removing duplicates
            deduped = []
            seen = set()
            for variant in variants:
                key = variant.lower().strip()
                if not key or key in seen:
                    continue
                seen.add(key)
                deduped.append(variant.strip())
            return deduped[:4]  # Limit to 4 variants max
        except Exception:
            # Fallback to simple variants
            return [query, query.lower()]

    @staticmethod
    def hyde_generate(query: str, llm) -> str:
        """
        HyDE (Hypothetical Document Embeddings).
        Generate a hypothetical perfect answer, then use that for retrieval.

        Best for: When questions are very different from document structure.
        Paper: https://arxiv.org/abs/2212.10496
        """
        prompt = f"""Write a passage that would answer this question:
Question: {query}

Passage:"""

        try:
            response = llm.invoke(prompt)
            if hasattr(response, 'content'):
                return response.content
            return str(response)
        except Exception as e:
            return query  # Fallback to original query
