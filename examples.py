"""
Example scripts and use cases for the AI Assistant
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import get_config
from assistant import AIAssistant


def example_basic_query():
    """Example 1: Basic query processing"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Query Processing")
    print("="*60)
    
    config = get_config()
    assistant = AIAssistant(config)
    
    query = "What is artificial intelligence?"
    print(f"\nQuery: {query}")
    
    try:
        result = assistant.process_query(query, use_rag=False, use_tools=False)
        print(f"\nResponse:\n{result['response']}")
    except Exception as e:
        print(f"Error: {e}")


def example_with_tools():
    """Example 2: Using tools"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Tool Calling")
    print("="*60)
    
    config = get_config()
    assistant = AIAssistant(config)
    
    query = "What is 42 multiplied by 3? Also, what's the current time?"
    print(f"\nQuery: {query}")
    
    try:
        result = assistant.process_query(query, use_rag=False, use_tools=True)
        print(f"\nResponse:\n{result['response']}")
        
        if result['tool_calls']:
            print(f"\nTools Called:")
            for call in result['tool_calls']:
                print(f"  - {call['tool_name']}: {call['tool_input']}")
        
        if result['tool_results']:
            print(f"\nTool Results:")
            for tool_name, result_str in result['tool_results'].items():
                print(f"  - {tool_name}: {result_str}")
    except Exception as e:
        print(f"Error: {e}")


def example_with_rag():
    """Example 3: RAG (Retrieval-Augmented Generation)"""
    print("\n" + "="*60)
    print("EXAMPLE 3: RAG (Knowledge Base Query)")
    print("="*60)
    
    config = get_config()
    assistant = AIAssistant(config)
    
    # Add sample documents
    sample_docs = [
        """
        Retrieval-Augmented Generation (RAG) is a technique that combines 
        information retrieval with language models. It retrieves relevant 
        documents and feeds them to the LLM for more accurate responses.
        RAG is useful for domain-specific applications and reducing hallucinations.
        """,
        """
        Vector databases like Chroma store embeddings of text documents.
        They enable semantic search by finding documents similar to a query.
        This is done by converting text to embeddings and computing similarity.
        Popular vector databases include Chroma, Pinecone, and Weaviate.
        """,
        """
        Embeddings are numerical representations of text that capture semantic meaning.
        Models like text-embedding-3-small convert text into high-dimensional vectors.
        Similar texts have similar embeddings, enabling semantic search.
        """
    ]
    
    print("\nAdding sample documents to knowledge base...")
    try:
        assistant.add_knowledge(sample_docs)
        
        query = "How does RAG work and what are vector databases?"
        print(f"\nQuery: {query}")
        
        result = assistant.process_query(query, use_rag=True, use_tools=False)
        print(f"\nResponse:\n{result['response']}")
        
        if result['rag_context']:
            print(f"\nRAG Context Used:\n{result['rag_context'][:500]}...")
    except Exception as e:
        print(f"Error: {e}")


def example_conversation():
    """Example 4: Multi-turn conversation"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Multi-Turn Conversation")
    print("="*60)
    
    config = get_config()
    assistant = AIAssistant(config)
    
    exchanges = [
        "What is machine learning?",
        "What are the main types of machine learning?",
        "Can you give examples of supervised learning?"
    ]
    
    print("\nStarting conversation...\n")
    try:
        for i, query in enumerate(exchanges, 1):
            print(f"Turn {i}:")
            print(f"  User: {query}")
            
            result = assistant.process_query(query, use_rag=False, use_tools=False)
            print(f"  Assistant: {result['response'][:200]}...")
            print()
    except Exception as e:
        print(f"Error: {e}")


def example_json_output():
    """Example 5: Structured JSON output"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Structured JSON Output")
    print("="*60)
    
    config = get_config()
    assistant = AIAssistant(config)
    
    query = """Create a JSON object for a book with these fields:
    title, author, year_published, pages, genres (as array), rating (1-10)"""
    
    print(f"\nQuery: {query}")
    
    try:
        result = assistant.generate_json_response(query)
        
        import json
        print(f"\nJSON Response:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Note: This example requires model with JSON mode support")
        print(f"Error: {e}")


def example_custom_tool():
    """Example 6: Custom tool registration"""
    print("\n" + "="*60)
    print("EXAMPLE 6: Custom Tool Registration")
    print("="*60)
    
    config = get_config()
    assistant = AIAssistant(config)
    
    # Define custom tool
    def get_word_count(text: str) -> int:
        """Count words in text"""
        return len(text.split())
    
    def string_reverse(text: str) -> str:
        """Reverse a string"""
        return text[::-1]
    
    # Register custom tools
    print("\nRegistering custom tools...")
    assistant.tool_registry.register_tool(
        name="word_counter",
        description="Count the number of words in a text",
        function=get_word_count,
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to count words in"}
            },
            "required": ["text"]
        }
    )
    
    assistant.tool_registry.register_tool(
        name="reverse_string",
        description="Reverse a string",
        function=string_reverse,
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to reverse"}
            },
            "required": ["text"]
        }
    )
    
    print("Custom tools registered!")
    print(f"Available tools: {assistant.tool_registry.list_tools()}")
    
    query = "How many words are in the text 'The quick brown fox jumps over the lazy dog'?"
    print(f"\nQuery: {query}")
    
    try:
        result = assistant.process_query(query, use_rag=False, use_tools=True)
        print(f"\nResponse:\n{result['response']}")
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("AI ASSISTANT - EXAMPLES")
    print("="*60)
    
    examples = [
        ("Basic Query", example_basic_query),
        ("Tool Calling", example_with_tools),
        ("RAG/Knowledge Base", example_with_rag),
        ("Conversation", example_conversation),
        ("JSON Output", example_json_output),
        ("Custom Tools", example_custom_tool),
    ]
    
    for i, (name, func) in enumerate(examples, 1):
        try:
            func()
        except Exception as e:
            print(f"\nExample {i} ({name}) failed: {e}")
        print("\n")
    
    print("="*60)
    print("Examples completed!")
    print("="*60)


if __name__ == "__main__":
    main()
