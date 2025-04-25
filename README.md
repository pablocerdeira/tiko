 # Tiko
 
 Tiko is a server that processes various types of documents and media files and provides concise summaries or text extraction. It integrates with tools such as Apache Tika for text extraction and Whisper for audio transcription when necessary. Tiko is designed to be agnostic regarding the language models (LLMs) and providers used. Configurations for LLM providers, Tika endpoints, and Whisper parameters are managed via a `config.json` file.
 
 ## Features
 
 - Extracts text from documents such as PDF, DOCX, XLSX, HTML, Markdown, and plain text.
 - Performs OCR on images with Tika if necessary.
 - Transcribes audio files using Whisper (if enabled).
 - Provides both summarization and full text extraction endpoints.
 - Supports processing of web URLs by downloading the content and sending it for extraction or summarization.
 
 ## Endpoints
 
 - **/summary**: Accepts a file or URL (via form field `file` or `url`) and returns a concise summary using a configurable LLM.
 - **/extract**: Accepts a file or URL and returns the extracted text without summarization.
 - **/health**: Returns the status of the server.
 
 ## Configuration
 
 Tiko uses a `config.json` file to configure parameters for:
  - The server (host, port, etc.)
  - Tika (extraction endpoints and OCR language)
  - Whisper (local transcription settings)
  - LLM providers (model, API keys, etc.)
 
 ## Usage
 
 To get started, run the server and then make requests using tools like `curl`. For example:
 
 ```bash
 curl -F "url=https://example.com" http://<server-address>:<port>/summary
 ```
 
 ## Requirements
 
 Tiko is designed to run on systems with Python 3.8+ and is compatible with various UNIX-like operating systems. Other dependencies are managed via installed packages.
 
 ## License
 
 This project is open source. See LICENSE for more information.
 
 version: 0.1.1
