"""
RAG (Retrieval-Augmented Generation) Pipeline components
"""
import os
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod


class DocumentLoader:
    """Loads documents from various sources"""

    @staticmethod
    def load_from_file(file_path: str) -> str:
        """Load text from a file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    @staticmethod
    def load_from_directory(directory: str, extension: str = ".txt") -> List[Dict[str, str]]:
        """Load all documents from a directory"""
        documents = []
        for filename in os.listdir(directory):
            if filename.endswith(extension):
                file_path = os.path.join(directory, filename)
                content = DocumentLoader.load_from_file(file_path)
                documents.append({
                    "content": content,
                    "source": filename,
                    "path": file_path
                })
        return documents

    @staticmethod
    def load_from_markdown(file_path: str) -> str:
        """Load markdown file"""
        return DocumentLoader.load_from_file(file_path)


class DocumentChunker:
    """Chunks documents into smaller pieces"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk = text[start:end]
            chunks.append(chunk)
            if end == len(text):
                break
            next_start = end - self.chunk_overlap
            start = max(next_start, start + 1)
        
        return chunks

    def chunk_by_sentences(self, text: str) -> List[str]:
        """Split text by sentences while respecting chunk size"""
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= self.chunk_size:
                current_chunk += " " + sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks


class BaseVectorStore(ABC):
    """Base class for vector stores"""

    @abstractmethod
    def add_texts(self, texts: List[str], metadata: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """Add texts to the vector store"""
        pass

    @abstractmethod
    def similarity_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        pass

    @abstractmethod
    def clear(self):
        """Clear all documents from the vector store"""
        pass


class ChromaVectorStore(BaseVectorStore):
    """Chroma vector store implementation"""

    def __init__(self, collection_name: str = "documents", embedding_model: str = "text-embedding-3-small"):
        try:
            import chromadb
            from chromadb.utils import embedding_functions
        except ImportError:
            raise ImportError("chromadb package is required. Install it with: pip install chromadb")

        persist_directory = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
        self.client = chromadb.PersistentClient(path=persist_directory)
        try:
            self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                api_key=os.getenv("API_KEY"),
                model_name=embedding_model
            )
        except:
            # Fallback to default embedding
            self.embedding_function = None

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )

    def add_texts(self, texts: List[str], metadata: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """Add texts with embeddings"""
        ids = [f"doc_{i}" for i in range(len(texts))]
        
        if metadata is None:
            metadata = [{} for _ in texts]

        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadata
        )
        return ids

    def similarity_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        results = self.collection.query(
            query_texts=[query],
            n_results=k
        )

        formatted_results = []
        if results and results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    "content": doc,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": results['distances'][0][i] if results['distances'] else 0
                })

        return formatted_results

    def clear(self):
        """Clear all documents"""
        self.client.delete_collection(name=self.collection.name)
        self.collection = self.client.create_collection(name=self.collection.name)


class Retriever:
    """Retrieves relevant documents from the vector store"""

    def __init__(self, vector_store: BaseVectorStore, top_k: int = 5):
        self.vector_store = vector_store
        self.top_k = top_k

    def retrieve(self, query: str) -> str:
        """Retrieve and format relevant documents"""
        results = self.vector_store.similarity_search(query, k=self.top_k)
        
        if not results:
            return "No relevant documents found."

        formatted = "Retrieved Documents:\n\n"
        for i, result in enumerate(results, 1):
            formatted += f"[Document {i}]\n{result['content']}\n\n"

        return formatted
