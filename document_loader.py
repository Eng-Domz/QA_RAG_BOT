"""
Document loading and processing module.
Handles multiple file formats and preprocessing.
"""
import os
from typing import List, Optional
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.document_loaders.word_document import Docx2txtLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import CHUNK_SIZE, CHUNK_OVERLAP


class DocumentProcessor:
    """
    Handles loading, splitting, and preprocessing of documents.
    """

    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def load_file(self, file_path: str) -> List[Document]:
        """
        Load a single file based on its extension.
        Supports: .pdf, .txt, .md, .docx
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        extension = path.suffix.lower()

        try:
            if extension == ".pdf":
                loader = PyPDFLoader(file_path)
            elif extension in [".txt", ".md"]:
                loader = TextLoader(file_path, encoding="utf-8")
            elif extension == ".docx":
                loader = Docx2txtLoader(file_path)
            else:
                print(f"Skipping unsupported file: {file_path}")
                return []

            documents = loader.load()

            # Add source metadata
            for doc in documents:
                doc.metadata["source_file"] = path.name
                doc.metadata["file_type"] = extension

            return documents

        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return []

    def load_directory(self, directory: str) -> List[Document]:
        """
        Load all supported files from a directory.
        """
        documents = []
        path = Path(directory)

        if not path.exists():
            print(f"Directory not found: {directory}")
            return documents

        supported_extensions = (".pdf", ".txt", ".md", ".docx")

        for file_path in path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                print(f"Loading: {file_path.name}")
                docs = self.load_file(str(file_path))
                documents.extend(docs)

        print(f"\nLoaded {len(documents)} document chunks from {directory}")
        return documents

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks for embedding.
        """
        if not documents:
            return []

        chunks = self.text_splitter.split_documents(documents)

        # Add chunk index per document for traceability
        current_doc_id = None
        chunk_counter = 0
        for chunk in chunks:
            source = chunk.metadata.get("source_file", "unknown")
            if source != current_doc_id:
                current_doc_id = source
                chunk_counter = 0
            chunk.metadata["chunk_index"] = chunk_counter
            chunk_counter += 1

        print(f"Split into {len(chunks)} chunks")
        return chunks

    def process(self, source: str) -> List[Document]:
        """
        Complete pipeline: load and split documents.
        Source can be a file or directory.
        """
        path = Path(source)

        if path.is_file():
            documents = self.load_file(source)
        elif path.is_dir():
            documents = self.load_directory(source)
        else:
            raise ValueError(f"Path not found: {source}")

        return self.split_documents(documents)
