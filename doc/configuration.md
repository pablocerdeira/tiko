# Tiko - Configuration Guide

This document details the configuration options available in the Tiko system.

## Configuration File

Tiko uses a `config.json` file for all its configurations. An example is available in `config-example.json`.

## Config.json Structure

```json
{
  "version": "0.4.1",
  "server": {
    "host": "0.0.0.0",
    "port": 9999
  },
  "tika": {
    "url": "http://localhost:9998",
    "ocr_language": "eng"
  },
  "whisper": {
    "enabled": true,
    "provider": "local",
    "model": "small",
    "language": "pt"
  },
  "llm": {
    "provider": "litellm",
    "providers": {
      "openai": { ... },
      "ollama": { ... },
      "litellm": { ... }
    }
  }
}
```

## Configuration Sections

### Server

HTTP server settings:

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `host` | string | IP address where the server will be available | "0.0.0.0" |
| `port` | int | Port where the server will be available | 9999 |

### Tika

Apache Tika settings for text extraction:

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `url` | string | Tika server URL | "http://localhost:9998" |
| `ocr_language` | string | Language code for OCR | "eng" |

### Whisper

Audio transcription settings:

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `enabled` | boolean | Enables/disables transcription | true |
| `provider` | string | Transcription provider ("local" or other) | "local" |
| `model` | string | Model size (tiny, base, small, medium, large) | "small" |
| `language` | string | Language code for transcription | "pt" |

### LLM

Language model settings:

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `provider` | string | Default provider (openai, ollama, litellm) | "litellm" |
| `providers` | object | Provider-specific settings | - |

#### Provider Configuration

Each provider can have its own configuration:

##### OpenAI

```json
"openai": {
  "url": "https://api.openai.com/v1/chat/completions",
  "api_key": "YOUR_OPENAI_API_KEY",
  "model": "gpt-3.5-turbo",
  "system_prompt": "You are a helpful assistant that summarizes text.",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

##### Ollama

```json
"ollama": {
  "url": "http://localhost:11434/v1/completions",
  "model": "llama2",
  "system_prompt": "You are a helpful assistant that summarizes text.",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

##### LiteLLM

```json
"litellm": {
  "url": "http://localhost:4000/v1/chat/completions",
  "api_key": "YOUR_LITELLM_API_KEY",
  "model": "gemini-2.0-flash",
  "model_refiner": "gpt-4.1-mini",
  "system_prompt": "You are an assistant that generates concise summaries of legal texts. When summarizing, produce a single response without headers or redundant information.",
  "temperature": 0.7,
  "max_tokens": 2000,
  "enable_pre_call_checks": true
}
```

## Common Parameters for LLM Providers

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | string | Provider API URL |
| `api_key` | string | API key for authentication |
| `model` | string | Model name to use |
| `model_refiner` | string | Optional model for refining results |
| `system_prompt` | string | System prompt to contextualize the LLM |
| `temperature` | float | Creativity control (0.0-1.0) |
| `max_tokens` | int | Maximum number of tokens in the response |

## Runtime Configuration Override

The `/summary` endpoint accepts query parameters that can temporarily override LLM settings:

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | Overrides the default model |
| `api_key` | string | Overrides the default API key |

Example:
```
POST /summary?model=gpt-4&api_key=your_api_key
```

## Configuration Reloading

The system monitors changes to the `config.json` file and automatically reloads the configuration when it detects changes, without the need to restart the service.