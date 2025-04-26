# Tiko - System Architecture

This document provides an overview of the Tiko system architecture, describing its main components, modules, and functions.

## Project Structure

```
tiko/
├── api/                 # REST API and web interface
│   ├── __init__.py
│   └── server.py        # Endpoint implementation
├── config/              # Specific configurations
├── core/               # Main components
│   ├── __init__.py
│   ├── extractor.py    # Text extraction from various formats
│   ├── graph.py        # Graph generation
│   ├── json.py         # JSON processing
│   ├── llm.py          # LLM integration
│   ├── summarizer.py   # Text summarization
│   ├── utils.py        # Utility functions
│   └── web_extractor.py # URL content extraction
├── schemas/            # Schemas to assist LLMs
└── tests/              # Automated tests
```

## Main Modules

### API (api/server.py)

Responsible for exposing HTTP endpoints and processing requests.

**Endpoints**:
- `/extract`: Extracts text from files or URLs
- `/summary`: Extracts and summarizes text from files or URLs
- `/json`: Extracts text and generates an ontological JSON structure
- `/health`: Checks server status

**Main Functions**:
- `get_config()`: Loads and updates configurations
- `process_request()`: Processes HTTP requests
- `extract()`: Implements the extraction endpoint
- `summary()`: Implements the summarization endpoint
- `json_response()`: Implements the ontological JSON generation endpoint

### Extraction Core (core/extractor.py)

Manages text extraction from different file types.

**Classes and Functions**:
- `Extractor`: Main extraction class
  - `extract_text_from_file()`: Extracts text from files
  - `extract_text_from_url()`: Extracts text from URLs
  - `extract_text_with_tika()`: Uses Tika for extraction
  - `extract_text_with_ocr()`: Performs OCR on images

### Summarization (core/summarizer.py)

Implements text summarization logic with advanced support for processing large documents.

**Classes and Functions**:
- `Summarizer`: Main class for summarization
  - `summarize_text()`: Summarizes text using LLM, initiating the chunking process when necessary
  - `summarize_file()`: Directly summarizes a file, extracting the text and starting the summarization process
  - `summarize_chunk()`: Implements the recursive chunking algorithm with dynamic adaptation

**Advanced Chunking Strategies**:
- Automatic division of large texts into chunks based on a configurable word limit (default: 80,000 words)
- Recursive processing for extensive texts, with dynamic adjustment of chunk size when the context is too large
- Intelligent combination of partial summaries into a cohesive text
- Detection of failures in processing large chunks and automatic size reduction
- Minimum chunking limit (1,000 words) to preserve sufficient context
- Use of refiner model (when configured) for the final summary stage, ensuring higher quality
- Intelligent estimation of final size based on available tokens in the model

This component allows efficient processing of very large documents (tens of MB), optimizing resource usage while maintaining high quality of the final result.

### LLM Integration (core/llm.py)

Manages communication with different LLM providers.

**Classes**:
- `LLMClient`: Base class for LLM clients
  - `get_client()`: Returns the appropriate client based on configuration
  - `generate_completion()`: Generates completions using LLM
  - `create_messages()`: Prepares messages for the LLM

### Web Extractor (core/web_extractor.py)

Responsible for downloading and processing web content.

**Functions**:
- `fetch_url()`: Downloads content from a URL
- `process_url()`: Processes URL for extraction
- `get_site_handler()`: Gets site-specific handler

### Utilities (core/utils.py)

Utility functions used throughout the system.

**Functions**:
- `detect_encoding()`: Detects text encoding
- `fix_encoding()`: Fixes encoding issues
- `format_log()`: Formats log messages in JSON

### Graph Generators (core/graph.py)

Implements knowledge graph generation.

**Classes**:
- `GraphGenerator`: Base for graph generators
  - `generate_graph()`: Generates graph from text
  - `export_json()`: Exports graph in JSON format

## Configuration (config-example.json)

Configuration file with the following sections:
- `server`: HTTP server settings
- `tika`: Apache Tika configuration
- `whisper`: Transcription system configuration
- `llm`: LLM provider configuration

## Schemas (schemas/*.json)

JSON schema documents used to guide LLM outputs:
- `fewshot_ontology_contrato.json`: Guidance for contract analysis
- `fewshot_ontology_decisao.json`: Guidance for judicial decision analysis
- `fewshot_ontology_geral.json`: General guidance
- `fewshot_ontology_leis_normas.json`: Guidance for legislation analysis
- `fewshot_ontology_parecer.json`: Guidance for legal opinion analysis
- `fewshot_ontology_peticao.json`: Guidance for petition analysis

## Data Flow

1. The client sends a file or URL to an endpoint (/extract or /summary)
2. The system identifies the content type
3. Extracts the text using the appropriate method (Tika, OCR, Whisper)
4. For summarization, the text is sent to the configured LLM
5. The result is returned to the client

## Upcoming Developments

According to the TODO.md file, upcoming developments include:
- Improvements in URL processing
- JSON output generation
- Creation of different types of graphs (citations, topics, knowledge)
- Customizable web interface
- Authentication system