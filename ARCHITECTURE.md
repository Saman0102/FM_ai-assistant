# AI Assistant Architecture Diagram

## High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE LAYER                          │
│                    (Python API / CLI / REST Endpoint)                   │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         AI ASSISTANT (MAIN ORCHESTRATOR)               │
│                                                                         │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────┐ │
│  │ Conversation Manager │  │  Config Manager     │  │ History      │ │
│  └──────────────────────┘  └──────────────────────┘  └──────────────┘ │
│                                                                         │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                ┌────────────┼────────────┐
                ▼            ▼            ▼
          ┌──────────┐ ┌──────────┐ ┌──────────────┐
          │   RAG    │ │   LLM    │ │    TOOLS     │
          │ Pipeline │ │ Provider │ │  Registry    │
          └──────────┘ └──────────┘ └──────────────┘
                │            │            │
         ┌──────┴─────┐     │       ┌─────┴─────┐
         ▼            ▼     │       ▼           ▼
    ┌────────┐  ┌─────────────────────────────┐  ┌────────────────┐
    │  Docs  │  │  LLM Providers              │  │  Tool Executor │
    │Loader/ │  ├─────────────────────────────┤  │                │
    │Chunker │  │ • OpenAI (GPT-4, etc.)      │  └────────────────┘
    │        │  │ • Claude (Anthropic)        │         │
    │        │  │ • Gemini (Google)           │    ┌────┴────────────┐
    └────────┘  │ • Bedrock (AWS)             │    ▼                ▼
         │      └─────────────────────────────┘  ┌────────┐  ┌────────────┐
         │                 │                     │Built-in│  │  Custom    │
         ▼                 ▼                     │Tools   │  │   Tools    │
    ┌──────────────┐  ┌─────────────────────┐  └────────┘  └────────────┘
    │Vector Store  │  │Response Processing   │       │
    │              │  │  ├─ JSON Parser     │      │
    │ • Chroma     │  │  ├─ Format Handler  │      │
    │ • Pinecone   │  │  └─ Output Manager  │      ▼
    │ • Weaviate   │  └─────────────────────┘  ┌─────────────┐
    └──────────────┘         │                 │  Results &   │
         │                   │                 │ Context Feed │
         ▼                   │                 └─────────────┘
    ┌──────────────┐         │                      │
    │  Retriever   │         │                      │
    │(Context      │         │                      │
    │ Generation)  │         │                      │
    └──────┬───────┘         │                      │
           │                 │                      │
           └─────────┬───────┴──────────────────────┘
                     ▼
          ┌────────────────────────────────┐
          │   Response Formatting & Output │
          ├────────────────────────────────┤
          │ • JSON Structured Response     │
          │ • Context-Aware Answer        │
          │ • Tool Call Summary            │
          │ • Conversation History Update  │
          └────────────────────────────────┘
                     │
                     ▼
          ┌─────────────────────────┐
          │   Return to User        │
          │  with Full Context      │
          └─────────────────────────┘
```

## Data Flow Diagram

```
┌─────────────────────┐
│   User Query        │
└──────────┬──────────┘
           │
           ▼
┌──────────────────────────────────────────────────────┐
│  Query Processing                                    │
│  • Input validation                                  │
│  • Conversation state loading                       │
└──────────────┬───────────────────────────────────────┘
               │
        ┌──────┴──────┐
        │             │
        ▼             ▼
   ┌─────────┐   ┌──────────┐
   │ RAG     │   │ Tool     │
   │Context  │   │Registry  │
   │Retrieval│   │Query     │
   └────┬────┘   └────┬─────┘
        │             │
        └──────┬──────┘
               ▼
   ┌──────────────────────────┐
   │ Prompt Engineering       │
   │ • System Prompt          │
   │ • Retrieved Context      │
   │ • Tool Definitions       │
   │ • Conversation History   │
   │ • User Query             │
   └──────────────┬───────────┘
                  │
                  ▼
   ┌──────────────────────────┐
   │ LLM Request              │
   │ • Formatted Messages     │
   │ • Tool Specifications    │
   │ • Generation Parameters  │
   └──────────────┬───────────┘
                  │
                  ▼
   ┌──────────────────────────┐
   │ LLM Response             │
   │ • Text Content           │
   │ • Tool Calls (optional)  │
   │ • Function Arguments     │
   └──────────────┬───────────┘
                  │
         ┌────────┴────────┐
         │                 │
      (Tool Calls?)       │
         │                 │
         ▼                 │
   ┌──────────────┐       │
   │ Tool         │       │
   │ Execution    │       │
   └────┬─────────┘       │
        │                 │
        ▼                 │
   ┌──────────────────┐   │
   │ Tool Results     │   │
   │ • Success/Error  │   │
   │ • Result Data    │   │
   └────┬─────────────┘   │
        │                 │
        └────────┬────────┘
                 ▼
   ┌──────────────────────────┐
   │ Response Finalization    │
   │ • Tool Results Injection │
   │ • Final LLM Call         │
   │ • Response Parsing       │
   └──────────────┬───────────┘
                  │
                  ▼
   ┌──────────────────────────┐
   │ Output Formatting        │
   │ • JSON Extraction        │
   │ • Context Preservation   │
   │ • History Update         │
   └──────────────┬───────────┘
                  │
                  ▼
   ┌──────────────────────────┐
   │ Return Result            │
   │ {                        │
   │   query,                 │
   │   response,              │
   │   rag_context,           │
   │   tool_calls,            │
   │   tool_results           │
   │ }                        │
   └──────────────────────────┘
```

## Component Interaction Diagram

```
                    ┌────────────────────────┐
                    │   AIAssistant          │
                    │   (Orchestrator)       │
                    └────────────┬───────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
    ┌────────┐          ┌──────────────┐        ┌──────────────┐
    │ Config │          │ Conversation │        │ Components   │
    │Manager │          │ Context      │        │  Registry    │
    └────────┘          └──────────────┘        └──────────────┘
        │                        │                   │  │  │
        │                        │                   │  │  └─────────────┐
        │                        │                   │  │                │
        │                        │                   ▼  ▼                ▼
        │                        │              ┌────────┐    ┌────────────┐
        │                        │              │  LLM   │    │   Tools    │
        │                        │              │ Client │    │  Registry  │
        │                        │              └────────┘    └────────────┘
        │                        │                   │               │
        │                        │                   ▼               ▼
        │                        │            ┌──────────────┐  ┌──────────┐
        │                        │            │   OpenAI     │  │  Tool    │
        │                        │            │   Claude     │  │Executor  │
        │                        │            │   Gemini     │  └──────────┘
        │                        │            │   Bedrock    │       │
        │                        │            └──────────────┘       ▼
        │                        │                                ┌─────────┐
        │                        │                                │Execute  │
        │                        │                                │Results  │
        │                        │                                └─────────┘
        │                        │
        └────────────────────────┼────────────────────────┐
                                 │                        │
                                 ▼                        ▼
                            ┌──────────────┐      ┌──────────────┐
                            │   RAG        │      │   Utils      │
                            │   Pipeline   │      │              │
                            └──────────────┘      └──────────────┘
                                 │                      │
                    ┌────────────┬┴────────────┐        │
                    │            │            │        │
                    ▼            ▼            ▼        ▼
            ┌──────────┐  ┌─────────────┐ ┌─────┐ ┌──────────┐
            │Document  │  │  Document   │ │Vector│ │ Prompt   │
            │Loader    │  │  Chunker    │ │Store │ │Manager   │
            └──────────┘  └─────────────┘ └──┬──┘ │ JSON     │
                                             │    │Parser    │
                                             ▼    └──────────┘
                                        ┌─────────┐
                                        │Retriever│
                                        └─────────┘
```

## RAG Pipeline Flow

```
┌─────────────────────────────────┐
│  Raw Documents                  │
│  • Text Files                   │
│  • PDFs                         │
│  • Markdown                     │
│  • Web Content                  │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Document Loader                │
│  • Load from filesystem         │
│  • Parse different formats      │
│  • Extract raw text             │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Text Preprocessing             │
│  • Cleaning                     │
│  • Normalization                │
│  • Deduplication                │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Document Chunking              │
│  • Sentence-level splitting     │
│  • Configurable chunk size      │
│  • Overlap for context          │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Embedding Generation           │
│  • text-embedding-3-small       │
│  • text-embedding-3-large       │
│  • Other models                 │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Vector Store Storage           │
│  • Chroma (default)             │
│  • Pinecone                     │
│  • Weaviate                     │
│  • Store with metadata          │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Query Time - Retrieval         │
│  1. Embed user query            │
│  2. Similarity search           │
│  3. Retrieve top-k chunks       │
│  4. Format context              │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Context Injection              │
│  • Prepend to LLM prompt        │
│  • Source attribution           │
│  • Relevance ranking            │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Enhanced LLM Response          │
│  • More accurate                │
│  • Grounded in documents        │
│  • Reduces hallucinations       │
└─────────────────────────────────┘
```

## Tool Calling Workflow

```
┌─────────────────┐
│  LLM Response   │
│  + Tool Calls   │
└────────┬────────┘
         │
         ▼
┌──────────────────────────────┐
│  Parse Tool Calls            │
│  Extract:                    │
│  • Tool Name                 │
│  • Input Parameters          │
│  • Call ID                   │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  Validate Against Registry   │
│  • Tool exists?              │
│  • Params valid?             │
│  • Permissions OK?           │
└────────┬─────────────────────┘
         │
    ┌────┴────┐
    │          │
(Valid)    (Invalid)
    │          │
    ▼          ▼
┌────────┐  ┌──────────┐
│Execute │  │  Return  │
└───┬────┘  │   Error  │
    │       └──────────┘
    │
    ▼
┌──────────────────────────────┐
│  Tool Execution              │
│  • Run function              │
│  • Capture output            │
│  • Handle exceptions         │
└────────┬─────────────────────┘
         │
    ┌────┴───────────┐
    │                │
 (Success)        (Error)
    │                │
    ▼                ▼
┌────────┐      ┌──────────┐
│ Result │      │  Error   │
│ Data   │      │  Message │
└───┬────┘      └────┬─────┘
    │                │
    └────────┬───────┘
             │
             ▼
┌──────────────────────────────┐
│  Context Feed Back to LLM    │
│  • Original query            │
│  • Tool results              │
│  • Request final response    │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  Final LLM Response          │
│  Incorporates tool results   │
└──────────────────────────────┘
```

## System Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Development Environment                   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  AI Assistant Source Code                           │  │
│  │  • Python modules (config, llm, rag, tools, etc.)  │  │
│  │  • Configuration files (.env)                      │  │
│  │  • Requirements.txt                                │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
          ┌────────────────────┐
          │   Docker Build     │
          │   docker build .   │
          └────────────┬───────┘
                       │
                       ▼
          ┌────────────────────────┐
          │  Docker Image          │
          │  ai-assistant:latest   │
          └────────────┬───────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
┌──────────────────┐      ┌──────────────────────┐
│  Local Container │      │  Cloud Deployment    │
│  dev env         │      │  (Task 2)            │
│  docker run      │      │  • AWS/GCP/Azure     │
└──────────────────┘      │  • Kubernetes        │
                          │  • Docker Compose    │
                          └──────────────────────┘
```

## Configuration & Deployment Options

```
┌─────────────────────────────────────────────┐
│  Configuration Management                   │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  .env File                           │  │
│  │  ├─ LLM Provider Selection          │  │
│  │  ├─ API Keys                        │  │
│  │  ├─ Model Parameters                │  │
│  │  ├─ RAG Settings                    │  │
│  │  └─ Debug Mode                      │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  Python Config Classes               │  │
│  │  ├─ LLMConfig                        │  │
│  │  ├─ RAGConfig                        │  │
│  │  └─ AssistantConfig                  │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  Runtime Configuration               │  │
│  │  ├─ Environment variables            │  │
│  │  ├─ CLI arguments                    │  │
│  │  └─ Config files                     │  │
│  └──────────────────────────────────────┘  │
│                                             │
└─────────────────────────────────────────────┘
```

## Error Handling & Resilience

```
┌─────────────────────────────────────────────┐
│  Error Handling Layers                      │
├─────────────────────────────────────────────┤
│                                             │
│  1. Input Validation                        │
│     └─ Check query format & size           │
│                                             │
│  2. Configuration Validation                │
│     └─ Verify API keys, settings           │
│                                             │
│  3. LLM Provider Error Handling             │
│     ├─ Network timeouts                    │
│     ├─ Rate limiting                       │
│     ├─ Invalid responses                   │
│     └─ Fallback mechanisms                 │
│                                             │
│  4. Tool Execution Error Handling           │
│     ├─ Tool not found                      │
│     ├─ Invalid parameters                  │
│     ├─ Execution failures                  │
│     └─ Graceful degradation                │
│                                             │
│  5. RAG Pipeline Error Handling             │
│     ├─ Document load failures              │
│     ├─ Embedding generation errors         │
│     ├─ Vector store failures               │
│     └─ No results fallback                 │
│                                             │
│  6. Response Parsing                        │
│     ├─ JSON parsing errors                 │
│     ├─ Format validation                   │
│     └─ Fallback formatting                 │
│                                             │
└─────────────────────────────────────────────┘
```

This architecture supports:

- ✅ Multiple LLM providers
- ✅ Pluggable vector databases
- ✅ Extensible tool system
- ✅ Flexible configuration
- ✅ Container deployment
- ✅ Error resilience
- ✅ Production readiness
