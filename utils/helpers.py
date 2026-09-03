"""
Utility functions for the AI Assistant
"""
import json
import re
from typing import Any, Dict, Optional


class JSONParser:
    """Parse and validate JSON from LLM responses"""

    @staticmethod
    def extract_json(text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from text"""
        # Try to find JSON in code blocks first
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find raw JSON
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    @staticmethod
    def ensure_json_serializable(obj: Any) -> Any:
        """Ensure object is JSON serializable"""
        if isinstance(obj, dict):
            return {k: JSONParser.ensure_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [JSONParser.ensure_json_serializable(item) for item in obj]
        elif isinstance(obj, set):
            return list(obj)
        elif hasattr(obj, '__dict__'):
            return str(obj)
        return obj


class PromptManager:
    """Manage prompt templates and generation"""

    @staticmethod
    def create_system_prompt(base_prompt: str, enable_rag: bool = False, 
                            enable_tools: bool = False, available_tools: list = None) -> str:
        """Create enhanced system prompt"""
        prompt = base_prompt

        if enable_rag:
            prompt += "\n\n[RAG MODE] You can use retrieved documents to answer questions. Always cite your sources."

        if enable_tools and available_tools:
            tools_list = ", ".join(available_tools)
            prompt += f"\n\n[TOOL ACCESS] You can use these tools: {tools_list}. Use tools when appropriate."

        prompt += "\n\n[OUTPUT] Always provide responses in valid JSON format when possible."

        return prompt

    @staticmethod
    def create_rag_prompt(question: str, context: str) -> str:
        """Create RAG-enhanced prompt"""
        return f"""Using the following context, answer the question:

Context:
{context}

Question: {question}

Provide a comprehensive answer based on the context. If the context doesn't contain relevant information, state that clearly."""

    @staticmethod
    def create_tool_prompt(query: str, tool_results: Dict[str, str]) -> str:
        """Create prompt with tool results"""
        prompt = f"Original query: {query}\n\nTool execution results:\n"
        for tool_name, result in tool_results.items():
            prompt += f"\n{tool_name}:\n{result}"
        return prompt
