# AI Assistant - Task 1: Applied AI

A robust AI assistant with LLM integration, RAG (Retrieval-Augmented Generation) pipeline, and tool calling capabilities.

## Features

✅ **LLM Integration**

- Support for multiple providers: OpenAI, Claude, Gemini, Bedrock
- Configurable temperature, top_p, and max_tokens
- Structured JSON output support
- Streaming capabilities (can be extended)

✅ **RAG Pipeline**

- Document loading from files and directories
- Smart chunking with sentence-level splitting and overlap
- Vector embeddings using Chroma vector database
- Semantic similarity search for context retrieval
- Metadata tracking for document sources

✅ **Tool Calling**

- Extensible tool registry system
- Built-in tools: calculator, current time
- Function calling with parameter validation
- Tool result handling and context feeding

✅ **Prompt Engineering**

- Customizable system prompts
- Context-aware prompt generation
- RAG context injection
- Tool availability declaration

✅ **Containerization**

- Docker support for easy deployment
- Minimal Python 3.11 base image
- All dependencies bundled

## Project Structure

```
ai_assistant/
├── config/                 # Configuration management
│   ├── config.py          # Settings and environment variables
│   └── __init__.py
├── llm/                   # LLM Provider Integration
│   ├── llm_client.py      # Abstract and concrete LLM clients
│   └── __init__.py
├── rag/                   # RAG Pipeline Components
│   ├── pipeline.py        # Document loader, chunker, vector store
│   └── __init__.py
├── tools/                 # Tool Calling System
│   ├── tool_registry.py   # Tool registration and execution
│   └── __init__.py
├── utils/                 # Utility Functions
│   ├── helpers.py         # JSON parser, prompt manager
│   └── __init__.py
├── data/                  # Data directory for documents
├── assistant.py           # Main AI Assistant class
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── .env.example          # Environment variables template
└── README.md             # This file
```

## Installation

### Local Setup

1. **Clone the repository**

   ```bash
   cd ai_assistant
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and settings
   ```

### Docker Setup

```bash
# Build image
docker build -t ai-assistant:latest .

# Run container
docker run --env-file .env ai-assistant:latest
```

## Configuration

Edit `.env` file with your settings:

```env
# LLM Configuration
LLM_PROVIDER=openai          # openai or claude
MODEL_NAME=gpt-4-turbo       # Model to use
API_KEY=your_api_key_here    # Your API key
TEMPERATURE=0.7              # Model creativity (0-1)
TOP_P=0.9                    # Nucleus sampling
MAX_TOKENS=2048              # Max response length

# RAG Configuration
EMBEDDING_MODEL=text-embedding-3-small
CHUNK_SIZE=1000
CHUNK_OVERLAP=100
TOP_K_RESULTS=5

# Debug Mode
DEBUG=false
```

## Usage

### Basic Usage

```python
from config import get_config
from assistant import AIAssistant

# Initialize
config = get_config()
assistant = AIAssistant(config)

# Simple query
result = assistant.process_query("What is machine learning?")
print(result['response'])
```

### With Knowledge Base

```python
# Add documents to knowledge base
documents = [
    "Python is a programming language...",
    "Machine learning is a field of AI..."
]
assistant.add_knowledge(documents)

# Query with RAG
result = assistant.process_query("Tell me about Python")
print(result['response'])
print(result['rag_context'])  # See what context was used
```

### Using Tools

```python
# Process query with tool calling
result = assistant.process_query("Calculate 15 * 12 and get current time")
print(result['response'])
print(result['tool_calls'])      # Tools that were called
print(result['tool_results'])    # Results from tools
```

### Custom Tools

```python
# Register custom tool
def get_weather(city: str) -> str:
    # Your implementation
    return f"Weather in {city}..."

assistant.tool_registry.register_tool(
    name="weather",
    description="Get weather for a city",
    function=get_weather,
    parameters={
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "City name"}
        },
        "required": ["city"]
    }
)
```

## Architecture

```
User Query
    ↓
┌───────────────────────┐
│  Input Processing    │
└───────────┬───────────┘
            ↓
    ┌───────────────────────────────────┐
    │  Parallel Processing              │
    │  ├─ RAG Retrieval (if enabled)   │
    │  └─ Tool Availability Check      │
    └───────────┬───────────────────────┘
                ↓
    ┌───────────────────────┐
    │  Prompt Engineering   │
    │  ├─ System Prompt    │
    │  ├─ RAG Context      │
    │  ├─ Conversation History
    │  └─ Tool Definitions │
    └───────────┬───────────┘
                ↓
    ┌───────────────────────┐
    │  LLM Generation       │
    │  ├─ OpenAI           │
    │  └─ Claude           │
    └───────────┬───────────┘
                ↓
    ┌───────────────────────┐
    │  Tool Execution       │
    │  (if tools called)    │
    └───────────┬───────────┘
                ↓
    ┌───────────────────────┐
    │  Response Generation  │
    │  ├─ JSON Parsing      │
    │  └─ Context Injection │
    └───────────┬───────────┘
                ↓
        User Receives Response
```

## Key Components

### 1. LLM Client (`llm/llm_client.py`)

- Abstract base class for LLM providers
- OpenAI implementation (GPT-4, etc.)
- Claude implementation (Anthropic)
- JSON structured output support
- Tool calling interface

### 2. RAG Pipeline (`rag/pipeline.py`)

- **DocumentLoader**: Load from files, directories, markdown
- **DocumentChunker**: Smart text chunking with overlap
- **ChromaVectorStore**: Vector embeddings and similarity search
- **Retriever**: Query processing and result formatting

### 3. Tool System (`tools/tool_registry.py`)

- **ToolRegistry**: Central tool management
- **ToolExecutor**: Tool execution with error handling
- **Built-in Tools**: Calculator, time, knowledge base search
- Extensible for custom tools

### 4. Assistant (`assistant.py`)

- Orchestrates all components
- Manages conversation state
- Handles multi-turn conversations
- Coordinates RAG and tool calling
- Implements response processing

## Examples

See `assistant.py` for running examples:

```bash
python assistant.py
```

This will execute:

1. Simple query example
2. Structured JSON output
3. RAG-based retrieval
4. Tool calling demonstration

## Future Enhancements

- [ ] Support for additional LLM providers (Gemini, Bedrock)
- [ ] Alternative vector databases (Pinecone, Weaviate)
- [x] Local model serving with vLLM (optional `local` Compose profile)
- [ ] Response streaming
- [ ] Conversation memory optimization
- [ ] Performance metrics and monitoring
- [ ] Web API interface (Uvicorn/FastAPI)
- [ ] Web UI (Streamlit/Gradio)
- [ ] Model fine-tuning pipeline
- [ ] Cost optimization and caching

## Error Handling

The assistant includes comprehensive error handling:

- Missing API keys detection
- Tool execution failures with graceful fallback
- Invalid JSON response parsing
- Rate limiting preparation
- Network timeout handling

## Performance Considerations

- Efficient chunk overlap for context preservation
- Similarity search optimization via Chroma
- Minimal token usage through smart prompting
- Configurable batch processing capabilities

## Dependencies

- **LLM**: openai, anthropic
- **RAG**: chromadb, langchain
- **Utils**: python-dotenv, pydantic
- **Dev**: pytest, black, flake8

## License

This project is part of FuseMachines AI Engineering curriculum.

## Support

For questions or issues:

1. Check the configuration (.env file)
2. Verify API keys are set correctly
3. Ensure dependencies are installed
4. Enable DEBUG mode for more information

## Task 2: Productionization

Task 2 is included in this project:

- Web UI and FastAPI backend (`api.py`, `static/index.html`)
- Async request handling with a thread pool
- Bounded in-memory response caching
- Retry with exponential backoff
- Per-client rate limiting
- Optional fallback LLM provider
- Docker Compose deployment
- Automated tests in `tests/`

### Run locally

```bash
cd ai_assistant
pip install -r requirements.txt
cp .env.example .env
# Set API_KEY in .env
uvicorn api:app --reload --port 8000
```

Open http://localhost:8000. API documentation is available at http://localhost:8000/docs.

### Run with Docker Compose

```bash
cd ai_assistant
cp .env.example .env
# Set API_KEY in .env
docker compose up --build
```

Open http://localhost:8000. Stop it with `docker compose down`.

### Requirement mapping

| Requirement                      | Implementation                            |
| -------------------------------- | ----------------------------------------- |
| Web UI                           | `static/index.html`                       |
| Backend connection               | FastAPI endpoints in `api.py`             |
| Concurrent/asynchronous requests | `asyncio.to_thread` in `/query`           |
| Prompt/response caching          | `TTLCache`                                |
| Retry mechanism                  | Exponential backoff in `AssistantService` |
| Rate limiting                    | Per-client `RateLimiter`                  |
| Fallback provider                | Optional `FALLBACK_*` settings            |
| Graceful errors                  | Health endpoint and HTTP error responses  |
| Docker deployment                | `Dockerfile` and `docker-compose.yml`     |
| Tests                            | `tests/test_api.py`                       |

ONNX conversion is not applicable to the current path because the application calls hosted LLM APIs rather than loading model weights locally.

### Run the local vLLM model

The project includes a vLLM service using the OpenAI-compatible API. To use it, change the LLM section in `.env`:

```env
LLM_PROVIDER=vllm
MODEL_NAME=Qwen/Qwen2.5-1.5B-Instruct
API_KEY=EMPTY
LLM_BASE_URL=http://vllm:8000/v1
```

You can copy the complete template with `cp .env.vllm.example .env`.

Then start both services with the `local` profile:

```bash
docker compose --profile local up --build
```

The assistant UI remains at http://localhost:8000. The vLLM API is available at http://localhost:8001/v1.

The default model is `Qwen/Qwen2.5-1.5B-Instruct`; change `VLLM_MODEL` and `MODEL_NAME` together when selecting another Hugging Face model. Private or gated models may require `HF_TOKEN` in `.env`.

vLLM normally requires a Linux host with an NVIDIA GPU and compatible NVIDIA Container Toolkit. Docker Desktop on macOS, especially Apple Silicon, is suitable for the Gemini configuration but generally cannot provide the CUDA environment required by this vLLM image. Run the local profile on a GPU-enabled Linux machine or cloud VM for the local-model demonstration.
