"""
Question Answering Chain implementation.
Connects retriever with LLM for RAG-based answers.
"""
from typing import List, Dict, Any

from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
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
)
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

        self.qa_chain = True

        print("QA Chain initialized!")
        return self

    def ask(self, question: str) -> Dict[str, Any]:
        """
        Ask a question and get an answer with sources.
        """
        if not self.qa_chain:
            raise RuntimeError("QA Chain not initialized. Call initialize_chain() first.")

        try:
            retrieved_docs = self.vectorstore_manager.similarity_search(question)

            if retrieved_docs:
                context = "\n\n".join(doc.page_content for doc in retrieved_docs)
                context_info = f"Retrieved {len(retrieved_docs)} document chunk(s)"
            else:
                context = ""
                context_info = "No relevant documents found"

            prompt = RAG_PROMPT.format(context=context, question=question)
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
        except Exception as e:
            return {
                "question": question,
                "answer": f"Error generating answer: {str(e)}",
                "context_info": "Error retrieving documents",
                "sources": [],
            }

    def debug_retrieval(self, question: str) -> None:
        """
        Debug helper: Show what documents were retrieved and their scores.
        """
        results = self.vectorstore_manager.similarity_search_with_scores(question)

        print(f"\n{'='*60}")
        print(f"DEBUG: Retrieval for question: '{question}'")
        print(f"{'='*60}\n")

        for i, (doc, score) in enumerate(results, 1):
            print(f"\n--- Result {i} (Score: {score:.4f}) ---")
            print(f"Source: {doc.metadata.get('source_file', 'Unknown')}")
            print(f"Content:\n{doc.page_content[:500]}...")
            print("-" * 60)
