"""
Tool calling and execution system
"""
import json
from typing import Any, Dict, List, Callable, Optional
from dataclasses import dataclass


@dataclass
class Tool:
    """Tool definition"""
    name: str
    description: str
    function: Callable
    parameters: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary format for LLM"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


class ToolRegistry:
    """Registry for managing tools"""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register_tool(self, name: str, description: str, function: Callable, 
                      parameters: Dict[str, Any]) -> None:
        """Register a new tool"""
        tool = Tool(
            name=name,
            description=description,
            function=function,
            parameters=parameters
        )
        self.tools[name] = tool

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a registered tool"""
        return self.tools.get(name)

    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """Get tools in LLM-compatible format"""
        return [tool.to_dict() for tool in self.tools.values()]

    def list_tools(self) -> List[str]:
        """List all registered tools"""
        return list(self.tools.keys())


class ToolExecutor:
    """Executes tool calls"""

    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """Execute a single tool"""
        tool = self.registry.get_tool(tool_name)
        
        if not tool:
            return f"Error: Tool '{tool_name}' not found"

        try:
            result = tool.function(**tool_input)
            return json.dumps({"success": True, "result": result})
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    def execute_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[str]:
        """Execute multiple tool calls"""
        results = []
        for tool_call in tool_calls:
            result = self.execute_tool(
                tool_call["tool_name"],
                tool_call["tool_input"]
            )
            results.append(result)
        return results


# Built-in tools
def calculator(operation: str, a: float, b: float) -> float:
    """Perform mathematical operations"""
    operations = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y if y != 0 else None,
    }
    return operations.get(operation, lambda x, y: None)(a, b)


def search_knowledge_base(query: str, retriever=None) -> str:
    """Search the knowledge base"""
    if retriever is None:
        return "Retriever not initialized"
    return retriever.retrieve(query)


def get_current_time() -> str:
    """Get current date and time"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def create_default_tools() -> ToolRegistry:
    """Create registry with default tools"""
    registry = ToolRegistry()

    registry.register_tool(
        name="calculator",
        description="Perform mathematical operations (add, subtract, multiply, divide)",
        function=calculator,
        parameters={
            "type": "object",
            "properties": {
                "operation": {"type": "string", "description": "Operation: add, subtract, multiply, divide"},
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"}
            },
            "required": ["operation", "a", "b"]
        }
    )

    registry.register_tool(
        name="get_time",
        description="Get current date and time",
        function=get_current_time,
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        }
    )

    return registry
