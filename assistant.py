"""
Main AI Assistant class that ties everything together
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import json

from config.config import AssistantConfig, get_config
from llm.llm_client import BaseLLMClient, create_llm_client, Message
from rag.pipeline import Retriever, DocumentChunker, ChromaVectorStore, DocumentLoader
from tools.tool_registry import ToolRegistry, ToolExecutor, create_default_tools
from utils.helpers import JSONParser, PromptManager


@dataclass
class ConversationContext:
    """Maintains conversation state"""
    messages: List[Message] = field(default_factory=list)
    tool_calls_history: List[Dict[str, Any]] = field(default_factory=list)

    def add_message(self, role: str, content: str):
        """Add a message to conversation"""
        self.messages.append(Message(role=role, content=content))

    def clear(self):
        """Clear conversation history"""
        self.messages.clear()
        self.tool_calls_history.clear()


class AIAssistant:
    """Main AI Assistant with RAG and Tool Calling capabilities"""

    def __init__(self, config: Optional[AssistantConfig] = None):
        self.config = config or get_config()
        self.conversation = ConversationContext()

        # Initialize LLM
        self.llm = create_llm_client(
            provider=self.config.llm.provider,
            api_key=self.config.llm.api_key,
            model=self.config.llm.model,
            temperature=self.config.llm.temperature,
            top_p=self.config.llm.top_p,
            max_tokens=self.config.llm.max_tokens
        )

        # Initialize RAG
        self.retriever = None
        if self.config.enable_rag:
            vector_store = ChromaVectorStore(
                embedding_model=self.config.rag.embedding_model
            )
            self.retriever = Retriever(
                vector_store=vector_store,
                top_k=self.config.rag.top_k_results
            )

        # Initialize Tools
        self.tool_registry = create_default_tools()
        self.tool_executor = ToolExecutor(self.tool_registry)

    def add_knowledge(self, documents: List[str], metadata: Optional[List[Dict[str, Any]]] = None):
        """Add documents to the knowledge base"""
        if not self.retriever:
            raise RuntimeError("RAG is not enabled")

        chunker = DocumentChunker(
            chunk_size=self.config.rag.chunk_size,
            chunk_overlap=self.config.rag.chunk_overlap
        )

        all_chunks = []
        all_metadata = []

        for i, doc in enumerate(documents):
            chunks = chunker.chunk_by_sentences(doc)
            all_chunks.extend(chunks)
            doc_metadata = metadata[i] if metadata else {}
            all_metadata.extend([doc_metadata] * len(chunks))

        self.retriever.vector_store.add_texts(all_chunks, all_metadata)
        print(f"Added {len(all_chunks)} chunks to knowledge base")

    def process_query(self, query: str, use_rag: bool = True, use_tools: bool = True) -> Dict[str, Any]:
        """Process a user query with RAG and tool calling"""
        # Add user message
        self.conversation.add_message("user", query)

        # Retrieve context if RAG is enabled
        rag_context = ""
        if use_rag and self.retriever:
            rag_context = self.retriever.retrieve(query)

        # Prepare messages
        messages = list(self.conversation.messages)

        # Add system prompt
        system_prompt = PromptManager.create_system_prompt(
            self.config.system_prompt,
            enable_rag=use_rag and self.config.enable_rag,
            enable_tools=use_tools and self.config.enable_tool_calling,
            available_tools=self.tool_registry.list_tools() if use_tools else []
        )
        messages.insert(0, Message(role="system", content=system_prompt))

        # Add RAG context if available
        if rag_context:
            messages.insert(1, Message(role="system", content=f"Retrieved Knowledge:\n{rag_context}"))

        # Get tools if enabled
        tools = self.tool_registry.get_tools_for_llm() if use_tools else None

        # Generate response
        response = self.llm.generate(
            messages=[Message(role=m.role, content=m.content) for m in messages],
            tools=tools
        )

        # Process tool calls if any
        tool_results = {}
        if response.get("tool_calls") and use_tools:
            for tool_call in response["tool_calls"]:
                result = self.tool_executor.execute_tool(
                    tool_call["tool_name"],
                    tool_call["tool_input"]
                )
                tool_results[tool_call["tool_name"]] = result
                self.conversation.tool_calls_history.append(tool_call)

            # If tools were called, make a follow-up request
            if tool_results:
                tool_prompt = PromptManager.create_tool_prompt(query, tool_results)
                messages.append(Message(role="user", content=tool_prompt))
                response = self.llm.generate(messages=messages)

        # Add assistant response to conversation
        self.conversation.add_message("assistant", response.get("content", ""))

        return {
            "query": query,
            "response": response.get("content", ""),
            "rag_context": rag_context,
            "tool_calls": response.get("tool_calls", []),
            "tool_results": tool_results
        }

    def generate_json_response(self, query: str) -> Dict[str, Any]:
        """Generate a structured JSON response"""
        self.conversation.add_message("user", query)

        messages = list(self.conversation.messages)
        system_prompt = PromptManager.create_system_prompt(
            self.config.system_prompt,
            enable_rag=self.config.enable_rag,
            enable_tools=False
        )
        messages.insert(0, Message(role="system", content=system_prompt))

        try:
            response = self.llm.generate_json(messages=[Message(role=m.role, content=m.content) for m in messages])
            self.conversation.add_message("assistant", json.dumps(response))
            return response
        except Exception as e:
            return {"error": str(e)}

    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation.clear()

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history"""
        return [{"role": m.role, "content": m.content} for m in self.conversation.messages]


def main():
    """Example usage"""
    # Initialize assistant
    config = get_config()
    assistant = AIAssistant(config)

    # Example 1: Simple query
    print("=== Example 1: Simple Query ===")
    result = assistant.process_query("What is 5 + 3?")
    print(f"Query: {result['query']}")
    print(f"Response: {result['response']}")
    print()

    # Example 2: Structured output
    print("=== Example 2: Structured Output ===")
    try:
        json_response = assistant.generate_json_response(
            "Create a JSON with fields: name, age, occupation"
        )
        print(json.dumps(json_response, indent=2))
    except Exception as e:
        print(f"Note: Structured output requires specific LLM setup: {e}")
    print()

    # Example 3: With knowledge base
    print("=== Example 3: RAG Query ===")
    if assistant.config.enable_rag:
        sample_docs = [
            "Python is a high-level programming language known for its simplicity and readability.",
            "Machine Learning is a subset of artificial intelligence that enables systems to learn from data."
        ]
        try:
            assistant.add_knowledge(sample_docs)
            result = assistant.process_query("Tell me about Python")
            print(f"Query: {result['query']}")
            print(f"Response: {result['response']}")
            if result['rag_context']:
                print(f"Context Used: {result['rag_context'][:200]}...")
        except Exception as e:
            print(f"RAG example skipped: {e}")
    print()

    # Example 4: Tool calling
    print("=== Example 4: Tool Calling ===")
    if assistant.config.enable_tool_calling:
        try:
            result = assistant.process_query("Calculate 15 * 12 and tell me what time it is")
            print(f"Query: {result['query']}")
            print(f"Response: {result['response']}")
            if result['tool_calls']:
                print(f"Tools Used: {[tc['tool_name'] for tc in result['tool_calls']]}")
        except Exception as e:
            print(f"Tool calling example: {e}")


if __name__ == "__main__":
    main()
