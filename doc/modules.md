# Tiko - Module Documentation

This document details the modules, classes, and functions of the Tiko system.

## API (api/server.py)

Module responsible for the HTTP interface of the system.

### Functions

| Function | Description |
|----------|-------------|
| `get_config()` | Loads and updates the configurations from the config.json file |
| `health()` | Implements the GET /health endpoint |
| `extract()` | Implements the POST /extract endpoint |
| `summary()` | Implements the POST /summary endpoint |
| `json_response()` | Implements the POST /json endpoint |
| `process_request()` | Processes HTTP requests, extracting file or URL |
| `create_app()` | Creates and configures the Flask application |
| `setup_logging()` | Configures the logging system |

### Endpoints

| Endpoint | Method | Parameters | Description |
|----------|--------|------------|-------------|
| `/health` | GET | - | Returns server status |
| `/extract` | POST | file or url | Extracts text from a file or URL |
| `/summary` | POST | file or url, model?, api_key? | Extracts and summarizes text |
| `/json` | POST | file or url, type? | Extracts text and generates ontological JSON structure |

## Core - Extractor (core/extractor.py)

Module for text extraction from different file types.

### Extractor Class

| Method | Description |
|--------|-------------|
| `__init__(self, config)` | Initializes with configurations |
| `extract_text_from_file(self, file_path)` | Extracts text from a file |
| `extract_text_from_url(self, url)` | Extracts text from a URL |
| `_detect_file_type(self, file_path)` | Detects the file type |
| `extract_text_with_tika(self, file_path)` | Extracts text using Tika |
| `extract_text_with_ocr(self, file_path)` | Extracts text with OCR via Tika |
| `transcribe_audio(self, file_path)` | Transcribes audio using Whisper |

## Core - Summarizer (core/summarizer.py)

Module for text summarization using LLMs.

### Summarizer Class

| Method | Description |
|--------|-------------|
| `__init__(self, config)` | Initializes with configurations |
| `summarize_file(self, file_path)` | Extracts and summarizes text from a file, handling files of any size |
| `summarize_text(self, text)` | Summarizes already extracted text, applying chunking strategies when necessary |
| `summarize_chunk(self, text, threshold)` | Implements the recursive chunking algorithm with adaptive word limit |


## Core - LLM (core/llm.py)

Module for integration with different LLM providers.

### LLMClient Class

| Method | Description |
|--------|-------------|
| `__init__(self, config)` | Initializes with configurations |
| `generate_completion(self, prompt, **kwargs)` | Generates completions using the LLM |
| `create_messages(self, prompt)` | Prepares messages for the model |
| `get_client(provider=None)` | Returns a client for the specified provider |

### Provider-Specific Classes

- `OpenAIClient`: Client for OpenAI
- `OllamaClient`: Client for Ollama
- `LiteLLMClient`: Client for LiteLLM

## Core - Web Extractor (core/web_extractor.py)

Module for downloading and processing web content.

### Functions

| Function | Description |
|----------|-------------|
| `fetch_url(url, config)` | Downloads content from a URL |
| `process_url(url, config)` | Processes URL for extraction |
| `get_site_handler(url, config)` | Gets site-specific handler |
| `save_temp_file(content, extension)` | Saves content to a temporary file |
| `get_temp_filename(extension)` | Generates a temporary filename |

## Core - Utils (core/utils.py)

Module with utility functions.

### Functions

| Function | Description |
|----------|-------------|
| `detect_encoding(text)` | Detects text encoding |
| `fix_encoding(text)` | Fixes encoding issues |
| `format_log(level, message, **kwargs)` | Formats logs in JSON |
| `clean_text(text)` | Removes unwanted characters |
| `chunk_text(text, chunk_size)` | Divides text into chunks of specific size |

## Core - JSON (core/json.py)

Module for ontological classification and JSON structure generation from documents.

### Functions

| Function | Description |
|----------|-------------|
| `generate_json(llm, text, graph_type)` | Generates structured JSON from text using few-shot templates |

The module loads JSON schema templates from the schemas/ directory to guide the LLM in generating ontological JSON structures specific to different types of legal documents:
- Contracts
- Judicial decisions
- Laws and regulations
- Legal opinions
- Petitions
- General documents

## Core - Graph (core/graph.py)

Module for knowledge graph generation.

### GraphGenerator Class

| Method | Description |
|--------|-------------|
| `__init__(self, config)` | Initializes with configurations |
| `generate_graph(self, text)` | Generates graph from text |
| `export_json(self)` | Exports graph in JSON format |

### Specific Classes

- `CitationGraph`: Generates citation graphs
- `KnowledgeGraph`: Generates knowledge graphs
- `TopicGraph`: Generates topic graphs


## Schemas (schemas/*.json)

JSON schemas for guiding LLMs.

| Schema | Description |
|--------|-------------|
| `fewshot_ontology_contrato.json` | Guidance for contract analysis |
| `fewshot_ontology_decisao.json` | Guidance for judicial decision analysis |
| `fewshot_ontology_geral.json` | General guidance |
| `fewshot_ontology_leis_normas.json` | Guidance for legislation analysis |
| `fewshot_ontology_parecer.json` | Guidance for legal opinion analysis |
| `fewshot_ontology_peticao.json` | Guidance for petition analysis |