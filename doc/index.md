# Tiko Documentation

Welcome to the Tiko documentation. This guide contains detailed information about the Tiko system architecture, configuration, and usage.

## Contents

- [Architecture](architecture.md) - Overview of the system architecture
- [Modules](modules.md) - Detailed description of modules, classes and functions
- [Configuration](configuration.md) - Complete configuration guide
- [Examples](examples.md) - Practical usage examples
- [Chunking](chunking.md) - Advanced chunking system for large documents

## Additional Resources

- [README.md](../README.md) - Quick start guide and overview
- [TODO.md](../TODO.md) - Planned features and improvements
- [config-example.json](../config-example.json) - Example configuration file

## Getting Started

1. Check the [README.md](../README.md) file for a basic overview
2. See [Architecture](architecture.md) for detailed system design
3. Review [Configuration](configuration.md) to set up your environment
4. Try the [Examples](examples.md) to get started quickly

## About Tiko

Tiko is a document processing system inspired by Apache Tika that provides:

1. **Text extraction** from various document formats (PDF, DOCX, XLSX, HTML, etc.)
2. **OCR** for images containing text
3. **Audio transcription** using Whisper
4. **Content summarization** using configurable LLMs

The system is designed to be:
- **Flexible**: supporting multiple formats and LLM providers
- **Scalable**: capable of processing documents of any size
- **Configurable**: allowing adjustments through a JSON file
- **Extensible**: with a modular architecture facilitating new features

---

Version: 0.4.1