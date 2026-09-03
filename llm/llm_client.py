"""
LLM Client for integrating with various LLM providers
"""
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Message:
    """Represents a message in conversation"""
    role: str  # system, user, assistant
    content: str


@dataclass
class ToolCall:
    """Represents a tool call from the model"""
    tool_name: str
    tool_input: Dict[str, Any]
    tool_use_id: str


class BaseLLMClient(ABC):
    """Base class for LLM clients"""

    def __init__(self, api_key: str, model: str, temperature: float = 0.7, 
                 top_p: float = 0.9, max_tokens: int = 2048):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens

    @abstractmethod
    def generate(self, messages: List[Message], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Generate response from the model"""
        pass

    @abstractmethod
    def generate_json(self, messages: List[Message]) -> Dict[str, Any]:
        """Generate structured JSON response"""
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI LLM Client"""

    def __init__(self, api_key: str, model: str = "gpt-4-turbo", base_url: str = "", **kwargs):
        super().__init__(api_key, model, **kwargs)
        try:
            from openai import OpenAI
            client_kwargs = {"api_key": api_key}
            if base_url:
                client_kwargs["base_url"] = base_url
            self.client = OpenAI(**client_kwargs)
        except ImportError:
            raise ImportError("openai package is required. Install it with: pip install openai")

    def generate(self, messages: List[Message], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Generate response using OpenAI API"""
        formatted_messages = [{"role": m.role, "content": m.content} for m in messages]
        
        kwargs = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
        }

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = self.client.chat.completions.create(**kwargs)
        
        result = {
            "content": response.choices[0].message.content,
            "tool_calls": []
        }

        # Extract tool calls if present
        if response.choices[0].message.tool_calls:
            for tool_call in response.choices[0].message.tool_calls:
                result["tool_calls"].append({
                    "tool_name": tool_call.function.name,
                    "tool_input": json.loads(tool_call.function.arguments),
                    "tool_use_id": tool_call.id
                })

        return result

    def generate_json(self, messages: List[Message]) -> Dict[str, Any]:
        """Generate structured JSON response"""
        formatted_messages = [{"role": m.role, "content": m.content} for m in messages]
        formatted_messages.append({
            "role": "user",
            "content": "Return your response as valid JSON only, no markdown or additional text."
        })

        response = self.client.chat.completions.create(
            model=self.model,
            messages=formatted_messages,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        return json.loads(content)


class VLLMClient(OpenAIClient):
    """Local vLLM server using its OpenAI-compatible API."""

    def __init__(self, api_key: str = "EMPTY", model: str = "Qwen/Qwen2.5-1.5B-Instruct",
                 base_url: str = "http://localhost:8001/v1", **kwargs):
        BaseLLMClient.__init__(self, api_key or "EMPTY", model, **kwargs)
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=api_key or "EMPTY",
                base_url=base_url,
            )
        except ImportError:
            raise ImportError("openai package is required for the vLLM-compatible API")


class ClaudeClient(BaseLLMClient):
    """Claude (Anthropic) LLM Client"""

    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229", **kwargs):
        super().__init__(api_key, model, **kwargs)
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=api_key)
        except ImportError:
            raise ImportError("anthropic package is required. Install it with: pip install anthropic")

    def generate(self, messages: List[Message], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Generate response using Claude API"""
        formatted_messages = [{"role": m.role, "content": m.content} for m in messages]

        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": formatted_messages,
            "system": messages[0].content if messages and messages[0].role == "system" else ""
        }

        if tools:
            kwargs["tools"] = tools

        response = self.client.messages.create(**kwargs)

        result = {
            "content": "",
            "tool_calls": []
        }

        for block in response.content:
            if hasattr(block, 'text'):
                result["content"] = block.text
            elif block.type == "tool_use":
                result["tool_calls"].append({
                    "tool_name": block.name,
                    "tool_input": block.input,
                    "tool_use_id": block.id
                })

        return result

    def generate_json(self, messages: List[Message]) -> Dict[str, Any]:
        """Generate structured JSON response"""
        formatted_messages = [{"role": m.role, "content": m.content} for m in messages]
        formatted_messages.append({
            "role": "user",
            "content": "Return your response as valid JSON only."
        })

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=formatted_messages
        )

        content = response.content[0].text
        return json.loads(content)


class GeminiClient(BaseLLMClient):
    """Google Gemini client using a Google AI Studio API key."""

    def __init__(self, api_key: str, model: str = "gemini-3.6-flash", **kwargs):
        super().__init__(api_key, model, **kwargs)
        try:
            from google import genai
            from google.genai import types
            self.genai = genai
            self.types = types
            self.client = genai.Client(api_key=api_key)
        except ImportError:
            raise ImportError("google-genai is required. Install it with: pip install google-genai")

    def _contents(self, messages: List[Message]):
        return [
            self.types.Content(
                role="user" if message.role == "user" else "model",
                parts=[self.types.Part.from_text(text=message.content)],
            )
            for message in messages
            if message.role != "system"
        ]

    def _config(self, system_prompt=None, tools=None, response_mime_type=None):
        function_declarations = []
        for tool in tools or []:
            function = tool.get("function", tool)
            function_declarations.append(
                self.types.FunctionDeclaration(
                    name=function["name"],
                    description=function.get("description", ""),
                    parameters=function.get("parameters"),
                )
            )
        tool_config = None
        if function_declarations:
            tool_config = [self.types.Tool(function_declarations=function_declarations)]
        return self.types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=self.temperature,
            top_p=self.top_p,
            max_output_tokens=self.max_tokens,
            tools=tool_config,
            response_mime_type=response_mime_type,
        )

    def generate(self, messages: List[Message], tools=None) -> Dict[str, Any]:
        system_prompt = next((message.content for message in messages if message.role == "system"), None)
        config = self._config(system_prompt=system_prompt, tools=tools)
        response = self.client.models.generate_content(
            model=self.model,
            contents=self._contents(messages),
            config=config,
        )
        result = {"content": response.text or "", "tool_calls": []}
        for candidate in response.candidates or []:
            for part in candidate.content.parts or []:
                if part.function_call:
                    result["tool_calls"].append({
                        "tool_name": part.function_call.name,
                        "tool_input": dict(part.function_call.args or {}),
                        "tool_use_id": part.function_call.name,
                    })
        return result

    def generate_json(self, messages: List[Message]) -> Dict[str, Any]:
        system_prompt = next((message.content for message in messages if message.role == "system"), None)
        config = self._config(
            system_prompt=system_prompt,
            response_mime_type="application/json",
        )
        response = self.client.models.generate_content(
            model=self.model,
            contents=self._contents(messages),
            config=config,
        )
        return json.loads(response.text)


def create_llm_client(provider: str, api_key: str, model: str, **kwargs) -> BaseLLMClient:
    """Factory function to create LLM client based on provider"""
    base_url = kwargs.pop("base_url", "")
    if provider.lower() == "openai":
        return OpenAIClient(api_key=api_key, model=model, base_url=base_url, **kwargs)
    elif provider.lower() == "claude":
        return ClaudeClient(api_key=api_key, model=model, **kwargs)
    elif provider.lower() in {"gemini", "google"}:
        return GeminiClient(api_key=api_key, model=model, **kwargs)
    elif provider.lower() in {"vllm", "local"}:
        return VLLMClient(
            api_key=api_key or "EMPTY",
            model=model or "Qwen/Qwen2.5-1.5B-Instruct",
            base_url=base_url or "http://localhost:8001/v1",
            **kwargs,
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")
