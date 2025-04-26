# Tiko - Chunking System for Large Documents

## Introduction

Tiko implements an advanced processing system to handle very large documents by dividing them into manageable parts (chunks) that are processed separately and then combined. This document details the implementation and operation of the chunking system.

## Chunking Process

Tiko's chunking algorithm is designed to handle documents of any size, including PDFs with thousands of pages or documents with tens of megabytes. The process occurs in several stages:

1. **Initial extraction**: Text is extracted from the document using the appropriate extractor
2. **Size verification**: The system analyzes if the text is too large to be processed at once
3. **Recursive division**: For large texts, the system divides the content into smaller chunks
4. **Summarization by chunk**: Each chunk is summarized individually
5. **Summary combination**: The partial summaries are combined
6. **Final refinement**: The combined summary is processed again to create a cohesive and concise version

## Detailed Algorithm

### 1. `summarize_text()` Method

This method is the entry point for the summarization process:

```python
def summarize_text(self, text):
    """Generate summary for given text using fallback strategy to handle context window errors."""
    return self.summarize_chunk(text, self.chunk_word_threshold)
```

### 2. `summarize_chunk()` Method

This is the heart of the recursive chunking algorithm:

```python
def summarize_chunk(self, text, threshold):
    """Recursively summarize the text using a given word threshold. Reduces chunk size if needed."""
    min_threshold = 1000  # Minimum chunk size to preserve context
    words = text.split()

    # If text is within the limit, try to summarize directly
    if len(words) <= threshold:
        summary = self.llm.summarize(text)
        if summary is not None:
            return summary
        else:
            # If it fails, reduce the threshold and try again
            if threshold > min_threshold:
                new_threshold = max(min_threshold, threshold // 2)
                return self.summarize_chunk(text, new_threshold)
            else:
                return None

    # If text is larger than the threshold, divide into chunks and summarize each one
    chunks = [" ".join(words[i:i+threshold]) for i in range(0, len(words), threshold)]
    summaries = []
    for chunk in chunks:
        chunk_summary = self.summarize_chunk(chunk, threshold)
        if chunk_summary:
            summaries.append(chunk_summary)

    # Combine summaries and check size again
    combined = "\n".join(summaries)
    if len(combined.split()) > threshold:
        new_threshold = max(min_threshold, threshold // 2)
        return self.summarize_chunk(combined, new_threshold)
    else:
        return combined
```

### 3. Final Refinement

To ensure a high-quality result, the system can apply a final refinement step using a more powerful LLM:

```python
# Final step: if the summary is too long, re-submit for a final concise summary
final_word_limit = int(self.llm.max_tokens * 0.75)
words_summary = summary.split()
if len(words_summary) > final_word_limit:
    prompt = ("From the summary below, produce a final summary that is cohesive and complete, "
              "including all relevant points, names of main parties involved, and maintaining "
              "important details, preferably maintaining chronology, but eliminating repetitions "
              "and redundant or unnecessary information. "
              "Summary: " + summary)
    final_summary = self.llm.summarize(prompt)
    if final_summary:
        summary = final_summary
```

## Chunking System Configuration

### Main Parameters

In the `config.json` file, you can configure:

```json
{
  "summarizer": {
    "chunk_word_threshold": 80000  // Default chunk size in words
  },
  "llm": {
    "providers": {
      "litellm": {
        "model": "gemini-2.0-flash",  // Primary model for chunks
        "model_refiner": "gpt-4.1-mini",  // More sophisticated model for final refinement
        "max_tokens": 4000  // Token limit in the response
      }
    }
  }
}
```

### Refiner Model

The system supports configuring a refiner model (`model_refiner`) that will be used specifically for the final stage. This allows using:

1. A more economical and faster model for summarizing individual chunks
2. A more sophisticated and higher quality model for the final refinement stage

## Benefits of the Approach

Tiko's chunking system offers several benefits:

1. **Scalability**: Files of any size can be processed
2. **Adaptability**: Automatic adjustment of chunk size in case of errors
3. **Efficiency**: Cost optimization using different models for different stages
4. **Robustness**: Failures in chunk processing are handled automatically
5. **Quality**: The final refinement process ensures a coherent and complete summary

## Practical Example

A 22MB PDF (approximately 600-700 pages) is processed as follows:

1. The extracted text has approximately 200,000 words
2. The system divides the text into 3 chunks of ~67,000 words each
3. Each chunk is summarized separately, generating partial summaries
4. The partial summaries are combined (~6,000 words)
5. The combined summary is refined to produce the final summary (~2,000 words)

This entire process occurs transparently to the user, who receives only the final concise and high-quality result.