"""
Configuration settings for the AI Assistant
"""
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LLMConfig:
    """LLM Configuration"""
    provider: str = os.getenv("LLM_PROVIDER", "gemini")  # gemini, openai, claude
    model: str = os.getenv("MODEL_NAME", "gemini-3.6-flash")
    api_key: str = os.getenv("API_KEY", "")
    base_url: str = os.getenv("LLM_BASE_URL", "")
    temperature: float = float(os.getenv("TEMPERATURE", "0.7"))
    top_p: float = float(os.getenv("TOP_P", "0.9"))
    max_tokens: int = int(os.getenv("MAX_TOKENS", "2048"))
    timeout: int = int(os.getenv("API_TIMEOUT", "30"))


@dataclass
class RAGConfig:
    """RAG Pipeline Configuration"""
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    embedding_dimension: int = int(os.getenv("EMBEDDING_DIMENSION", "1536"))
    vector_db_type: str = os.getenv("VECTOR_DB_TYPE", "chroma")  # chroma, pinecone, weaviate
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "100"))
    top_k_results: int = int(os.getenv("TOP_K_RESULTS", "5"))


@dataclass
class AssistantConfig:
    """Main Assistant Configuration"""
    llm: LLMConfig = field(default_factory=LLMConfig)
    rag: RAGConfig = field(default_factory=RAGConfig)
    system_prompt: str = """You are an intelligent AI assistant capable of answering questions, 
reasoning about problems, and using tools to complete tasks. 
You provide accurate and helpful responses in clear, concise natural language.
Return JSON only when the user explicitly requests structured JSON output."""
    enable_tool_calling: bool = True
    enable_rag: bool = True
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"


def get_config() -> AssistantConfig:
    """Get the assistant configuration"""
    return AssistantConfig()
