# Tiko

Tiko is a powerful hub designed to efficiently process files and documents. Its name is a playful nod to Apache Tika, reflecting its deep integration with Tika's extraction and OCR capabilities. It supports advanced text extraction from a variety of document formats, robust OCR on images, and high-quality audio transcription via Whisper, which can run both locally and remotely.

This system serves as an essential backend service for chat bots, document management systems, automated email processing, and more. It supports processing massive documents through advanced chunking strategies – for example, a PDF with over 2000 pages is automatically divided into manageable chunks, each summarized separately, with the intermediate summaries then combined and refined using a more sophisticated LLM. This multi-stage approach ensures efficient processing while maintaining high-quality output, even for documents exceeding 20MB in size.
 
 ## Features
 
 - Extracts text from documents such as PDF, DOCX, XLSX, HTML, Markdown, and plain text.
 - Performs OCR on images with Tika if necessary.
 - Transcribes audio files using Whisper (if enabled).
 - Provides both summarization and full text extraction endpoints.
 - Supports processing of web URLs by downloading the content and sending it for extraction or summarization.
 
 ## Endpoints
 
 - **/summary**: Accepts a file or URL (via form field `file` or `url`) and returns a concise summary using a configurable LLM. Requires a valid token.
 - **/extract**: Accepts a file or URL and returns the extracted text without summarization. Requires a valid token.
 - **/json**: Accepts a file or URL and returns an ontological JSON structure based on the document type. Requires a valid token.
 - **/health**: Returns the status and version of the server. Requires a valid token.
 
## Configuration

Tiko uses a `config.json` file to configure parameters for:
  - The server (host, port, etc.)
  - Tika (extraction endpoints and OCR language)
  - Whisper (local transcription settings)
  - LLM providers (model, API keys, etc.)

## Detailed Configuration (config.json)

The `config.json` file is crucial for tailoring Tiko to your environment. Below are the available configuration sections with detailed explanations and examples:

### 1. Server Configuration

Settings for the Tiko server. Example:

```json
"server": {
  "host": "0.0.0.0",   // The IP address to bind the server (use 0.0.0.0 to listen on all interfaces)
  "port": 9999         // The port number where Tiko will accept requests
}
```

### 2. Tika Configuration

Configuration for Apache Tika which handles text extraction, OCR, and more. Example:

```json
"tika": {
  "url": "http://localhost:9998", // The endpoint URL where Apache Tika is running
  "ocr_language": "eng"             // Default language code for OCR operations (use ISO codes, e.g., 'eng', 'por')
}
```

### 3. Whisper Configuration

Settings for audio transcription. This section enables transcription via Whisper. Example:

```json
"whisper": {
  "enabled": true,       // Set to true to enable audio transcription
  "provider": "local",   // Specifies the transcription provider (e.g., 'local' or a remote service identifier)
  "model": "small",      // Model size to use for transcription (options might include: tiny, base, small, medium, large)
  "language": "pt"       // Language of the audio file (use ISO language codes like 'pt' for Portuguese)
}
```

### 4. LLM Configuration

This section configures the Large Language Models used for summarization. Tiko is designed to be agnostic, supporting multiple providers. Here is an example structure:

```json
"llm": {
  "provider": "litellm", // Default LLM provider to use if none is specified in the request
  "providers": {
    "openai": {
      "url": "https://api.openai.com/v1/chat/completions",
      "api_key": "YOUR_OPENAI_API_KEY",  // API key for authenticating with OpenAI
      "model": "gpt-3.5-turbo",
      "system_prompt": "You are a helpful assistant that summarizes text.",
      "temperature": 0.7,
      "max_tokens": 2000
    },
    "ollama": {
      "url": "http://localhost:11434/v1/completions",
      "model": "llama2",
      "system_prompt": "You are a helpful assistant that summarizes text.",
      "temperature": 0.7,
      "max_tokens": 2000
    },
    "litellm": {
      "url": "http://localhost:4000/v1/chat/completions",
      "api_key": "YOUR_LITELLM_API_KEY",
      "model": "gemini-2.0-flash", // Default model
      "model_refiner": "gpt-4.1-mini", // Optional: used to refine the output if necessary
      "system_prompt": "You are an assistant that generates concise summaries of legal texts. When summarizing, produce a single response without headers or redundant information.",
      "temperature": 0.7,
      "max_tokens": 2000,
      "enable_pre_call_checks": true  // Optional: perform pre-call validations before sending requests
    }
  }
}
```

Each provider can be configured independently. Adjust the parameters as needed based on cost, performance, and specific model requirements.

---

## Usage

 To get started, run the server and then make requests using tools like `curl`.

 ### Using URLs

 You can pass a URL directly to either endpoint. For instance, to summarize the content of a web page:

 ```bash
 curl -F "url=https://example.com" "http://<server-address>:<port>/summary?token=YOUR_API_TOKEN"
 ```

 And to extract the full text from a URL:

 ```bash
 curl -F "url=https://example.com" "http://<server-address>:<port>/extract?token=YOUR_API_TOKEN"
 ```

### Using Files

The endpoints also accept file uploads. Below are examples for different file types:

#### PDF Files

To summarize a PDF document:

```bash
curl -X POST -F "file=@/path/to/document.pdf" "http://<server-address>:<port>/summary?token=YOUR_API_TOKEN"
```

To extract the full text from a PDF:

```bash
curl -X POST -F "file=@/path/to/document.pdf" "http://<server-address>:<port>/extract?token=YOUR_API_TOKEN"
```

#### DOCX Files

To summarize a DOCX file:

```bash
curl -X POST -F "file=@/path/to/document.docx" "http://<server-address>:<port>/summary?token=YOUR_API_TOKEN"
```

To extract text from a DOCX file:

```bash
curl -X POST -F "file=@/path/to/document.docx" "http://<server-address>:<port>/extract?token=YOUR_API_TOKEN"
```

#### Images

For image files, Tiko can perform OCR to extract text. To summarize an image:

```bash
curl -X POST -F "file=@/path/to/image.jpg" "http://<server-address>:<port>/summary?token=YOUR_API_TOKEN"
```

And to extract text using OCR:

```bash
curl -X POST -F "file=@/path/to/image.png" "http://<server-address>:<port>/extract?token=YOUR_API_TOKEN"
```

### Custom Request Parameters

#### Authentication

All endpoints require a valid authentication token passed as a URL query parameter:

 - ?token=<your_token> : Your API access token. This is required for all API calls.

#### Summary Endpoint Parameters

The /summary endpoint supports per-request customization of the LLM settings via URL query parameters. You can override default LLM settings as follows:

 - ?model=<model_name> : Overrides the default LLM model. For example, if you want to use 'gpt-4' for a specific request, append ?model=gpt-4 to the URL.

 - ?api_key=<your_api_key> : Provides a specific API key for the LLM provider for that request. This is useful if you want to use dynamic credentials.

#### JSON Endpoint Parameters

The /json endpoint supports the following parameter:

 - ?type=<document_type> : Specifies the document type for more accurate JSON generation. 
   - Standard types: 'contrato', 'decisao', 'leis_normas', 'parecer', 'peticao', or 'geral'
   - Custom types: You can specify any type that matches files in the schemas directory. For example, using ?type=imoveis will use the models fewshot_ontology_imoveis.json and exemplo_ontology_imoveis.json if they exist.

For example, to make a request with both authentication and parameter overrides:

```bash
curl -X POST -F "file=@/path/to/document.pdf" "http://<server-address>:<port>/summary?token=YOUR_API_TOKEN&model=gpt-4&api_key=YOUR_API_KEY"
```

When these parameters are provided, Tiko creates a temporary summarizer instance with the overrides applied, ensuring that the request uses the specified settings without affecting the global configuration.

---

## Requirements

Tiko is designed to run on systems with Python 3.8+ and is compatible with various UNIX-like operating systems. Other dependencies are managed via installed packages.

## Installation Recommendations

  - Apache Tika: Required for Tiko's text extraction and OCR functionalities. Ensure that Apache Tika is properly installed and configured.
  - LiteLLM: Recommended for controlling costs and enabling multi-LLM workflows, ideal for processing large documents and optimizing summarization strategies.
 
## License

This project is open source. See LICENSE for more information.
 
 version: 0.6.0
