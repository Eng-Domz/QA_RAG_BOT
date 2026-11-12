"""
Question Answering Chain implementation.
Connects retriever with LLM for RAG-based answers.
"""
from typing import Dict, Any, List, Set, Tuple

from langchain_core.prompts import PromptTemplate
from langchain_community.llms.ollama import Ollama
from langchain_openai import ChatOpenAI

from config import (
    OPENAI_API_KEY,
    LLM_MODEL,
    LLM_TEMPERATURE,
    MAX_TOKENS,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    USE_GPU,
    TOP_K,
    SIMILARITY_THRESHOLD,
    RETRIEVAL_MODE,
    HYBRID_WEIGHTS,
    ENABLE_QUERY_EXPANSION,
    ENABLE_HYDE,
    MAX_QUERY_VARIANTS,
    STRICT_GROUNDING,
    FALLBACK_TO_TOP_K_IF_BELOW_THRESHOLD,
)
from advanced_rag import AdvancedRetriever, QueryExpansion
from vectorstore import VectorStoreManager


# RAG Prompt Template - Improved for better answer quality
RAG_PROMPT_TEMPLATE = """You are a helpful AI assistant answering questions based on the provided context.

Instructions:
1. Use the context below as your PRIMARY source of information
2. Answer based on the context when possible, but also use your general knowledge to provide helpful responses
3. If the context doesn't contain enough information, say so but still try to provide a helpful answer from your knowledge
4. Be concise, specific, and practical
5. Mention the source file when the answer comes from the context
6. If context and general knowledge seem to conflict, note this in your answer

Context from documents:
{context}

Question: {question}

Answer:"""

RAG_PROMPT = PromptTemplate(
    template=RAG_PROMPT_TEMPLATE,
    input_variables=["context", "question"],
)

STRICT_RAG_PROMPT_TEMPLATE = """You are a retrieval-grounded assistant.

Instructions:
1. Answer ONLY using the context below.
2. If context is insufficient, explicitly say you don't have enough grounded information.
3. Do NOT use external or general knowledge.
4. Provide a concise answer and cite source file names when possible.

Context from documents:
{context}

Question: {question}

Grounded answer:"""

STRICT_RAG_PROMPT = PromptTemplate(
    template=STRICT_RAG_PROMPT_TEMPLATE,
    input_variables=["context", "question"],
)


class QABot:
    """
    Main QA Bot class that combines retrieval and generation.
    """

    def __init__(
        self,
        vectorstore_manager: VectorStoreManager,
        use_openai: bool = True,
        use_ollama: bool = False,
    ):
        self.vectorstore_manager = vectorstore_manager
        self.llm = self._initialize_llm(use_openai, use_ollama)
        self.qa_chain = None
        self.retrieval_mode = RETRIEVAL_MODE if RETRIEVAL_MODE in {"standard", "hybrid"} else "standard"
        self.advanced_retriever = AdvancedRetriever(vectorstore_manager)

    def _initialize_llm(self, use_openai: bool, use_ollama: bool):
        """
        Initialize the language model.
        """
        if use_openai and OPENAI_API_KEY:
            print(f"Using OpenAI model: {LLM_MODEL}")
            return ChatOpenAI(
                model=LLM_MODEL,
                temperature=LLM_TEMPERATURE,
                max_tokens=MAX_TOKENS,
                api_key=OPENAI_API_KEY,
            )
        elif use_ollama:
            gpu_info = " (GPU accelerated)" if USE_GPU else ""
            print(f"Using Ollama model: {OLLAMA_MODEL}{gpu_info}")
            print(f"Ollama base URL: {OLLAMA_BASE_URL}")
            return Ollama(
                model=OLLAMA_MODEL,
                base_url=OLLAMA_BASE_URL,
                temperature=LLM_TEMPERATURE,
            )
        else:
            raise ValueError(
                "No LLM available. Please set OPENAI_API_KEY or install Ollama."
            )

    def initialize_chain(self):
        """
        Validate bot readiness.
        """
        if not self.vectorstore_manager.vectorstore:
            raise RuntimeError("Vector store not initialized")

        if self.retrieval_mode == "hybrid":
            self.advanced_retriever.setup_hybrid_search(weights=HYBRID_WEIGHTS)
            print(f"Retrieval mode: hybrid (weights={HYBRID_WEIGHTS})")
        else:
            print("Retrieval mode: standard")

        self.qa_chain = True

        print("QA Chain initialized!")
        return self

    def _build_query_set(self, question: str) -> List[str]:
        """
        Build query set from original question + optional expansion/HyDE.
        """
        queries: List[str] = [question]

        if ENABLE_QUERY_EXPANSION:
            queries.extend(QueryExpansion.generate_variants(question, llm=self.llm))

        if ENABLE_HYDE:
            queries.append(QueryExpansion.hyde_generate(question, self.llm))

        deduped: List[str] = []
        seen: Set[str] = set()
        for q in queries:
            cleaned = (q or "").strip()
            if not cleaned:
                continue
            key = cleaned.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(cleaned)

        return deduped[:max(1, MAX_QUERY_VARIANTS)]

    @staticmethod
    def _doc_key(doc) -> Tuple[str, Any, str]:
        chunk_id = doc.metadata.get("chunk_id")
        if chunk_id:
            return (str(chunk_id), 0, "")
        source = doc.metadata.get(
            "source_path", doc.metadata.get("source_file", "unknown")
        )
        chunk_index = doc.metadata.get("chunk_index", -1)
        content_head = doc.page_content[:120]
        return (source, chunk_index, content_head)

    def _retrieve_documents(self, question: str) -> Tuple[List, int]:
        """
        Retrieve context documents using configured retrieval strategy.
        """
        queries = self._build_query_set(question)
        all_docs = []

        for query in queries:
            if self.retrieval_mode == "hybrid" and self.advanced_retriever.ensemble_retriever:
                if STRICT_GROUNDING:
                    # BM25 and vector scores are not directly comparable. Require at
                    # least one semantically relevant result before accepting the
                    # hybrid ranking for a grounded answer.
                    semantic_gate = self.vectorstore_manager.similarity_search(
                        query,
                        k=TOP_K,
                        similarity_threshold=SIMILARITY_THRESHOLD,
                        fallback_to_top_k=False,
                    )
                    if not semantic_gate:
                        continue
                docs = self.advanced_retriever.retrieve(query, method="hybrid")
                if STRICT_GROUNDING:
                    allowed_keys = {self._doc_key(doc) for doc in semantic_gate}
                    docs = [doc for doc in docs if self._doc_key(doc) in allowed_keys]
            else:
                docs = self.vectorstore_manager.similarity_search(
                    query,
                    k=TOP_K,
                    similarity_threshold=SIMILARITY_THRESHOLD,
                    fallback_to_top_k=(
                        FALLBACK_TO_TOP_K_IF_BELOW_THRESHOLD and not STRICT_GROUNDING
                    ),
                )
            all_docs.extend(docs)

        deduped_docs = []
        seen_keys = set()
        for doc in all_docs:
            key = self._doc_key(doc)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            deduped_docs.append(doc)

        # Keep context bounded to reduce token cost.
        return deduped_docs[:TOP_K], len(queries)

    def ask(self, question: str) -> Dict[str, Any]:
        """
        Ask a question and get an answer with sources.
        """
        if not self.qa_chain:
            raise RuntimeError("QA Chain not initialized. Call initialize_chain() first.")

        try:
            retrieved_docs, query_count = self._retrieve_documents(question)

            if retrieved_docs:
                context = "\n\n".join(doc.page_content for doc in retrieved_docs)
                context_info = (
                    f"Retrieved {len(retrieved_docs)} chunk(s) using "
                    f"{self.retrieval_mode} retrieval over {query_count} query variant(s)"
                )
            else:
                context = ""
                context_info = "No relevant documents found"

            if STRICT_GROUNDING and not retrieved_docs:
                return {
                    "question": question,
                    "answer": (
                        "I do not have enough grounded context in the indexed documents "
                        "to answer this reliably."
                    ),
                    "context_info": context_info,
                    "sources": [],
                }

            prompt_template = STRICT_RAG_PROMPT if STRICT_GROUNDING else RAG_PROMPT
            prompt = prompt_template.format(context=context, question=question)
            llm_response = self.llm.invoke(prompt)
            answer = llm_response.content if hasattr(llm_response, "content") else str(llm_response)

            return {
                "question": question,
                "answer": answer,
                "context_info": context_info,
                "sources": [
                    {
                        "content": doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content,
                        "metadata": doc.metadata,
                    }
                    for doc in retrieved_docs
                ],
            }
        except Exception as exc:
            raise RuntimeError(
                f"Failed to answer question {question!r}: {exc}"
            ) from exc

    def debug_retrieval(self, question: str) -> None:
        """
        Debug helper: Show what documents were retrieved and their scores.
        """
        results = self.vectorstore_manager.similarity_search_with_scores(question)

        print(f"\n{'='*60}")
        print(f"DEBUG: Retrieval for question: '{question}'")
        print(f"Mode: {self.retrieval_mode} | strict_grounding={STRICT_GROUNDING}")
        print(f"{'='*60}\n")

        for i, (doc, score) in enumerate(results, 1):
            print(f"\n--- Result {i} (Score: {score:.4f}) ---")
            print(
                "Source: "
                f"{doc.metadata.get('source_path', doc.metadata.get('source_file', 'Unknown'))}"
            )
            print(f"Content:\n{doc.page_content[:500]}...")
            print("-" * 60)
