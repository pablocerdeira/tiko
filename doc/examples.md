# Tiko - Usage Examples

This document presents practical examples of how to use Tiko for document processing and summarization.

## Usage via Curl

### Text Extraction

#### Extract from a PDF File

```bash
curl -X POST -F "file=@/path/to/document.pdf" http://localhost:9999/extract
```

#### Extract from a URL

```bash
curl -X POST -F "url=https://example.com/page.html" http://localhost:9999/extract
```

### Summarization

#### Summarize a PDF File

```bash
curl -X POST -F "file=@/path/to/document.pdf" http://localhost:9999/summary
```

#### Summarize a URL

```bash
curl -X POST -F "url=https://example.com/page.html" http://localhost:9999/summary
```

#### Summarize with a Specific Model

```bash
curl -X POST -F "file=@/path/to/document.pdf" "http://localhost:9999/summary?model=gpt-4"
```

#### Summarize with a Custom API Key

```bash
curl -X POST -F "file=@/path/to/document.pdf" "http://localhost:9999/summary?api_key=your_api_key"
```

### Ontological JSON Generation

#### Generate JSON from a PDF File

```bash
curl -X POST -F "file=@/path/to/document.pdf" http://localhost:9999/json
```

#### Generate JSON from a URL

```bash
curl -X POST -F "url=https://example.com/page.html" http://localhost:9999/json
```

#### Generate JSON with a Specific Type

```bash
curl -X POST -F "file=@/path/to/document.pdf" "http://localhost:9999/json?type=decisao"
```

### Check Server Status

```bash
curl http://localhost:9999/health
```

## Examples by File Type

### PDF Documents

```bash
# Simple extraction
curl -X POST -F "file=@document.pdf" http://localhost:9999/extract

# Summarization
curl -X POST -F "file=@document.pdf" http://localhost:9999/summary
```

### Word Documents (DOCX)

```bash
# Simple extraction
curl -X POST -F "file=@document.docx" http://localhost:9999/extract

# Summarization
curl -X POST -F "file=@document.docx" http://localhost:9999/summary
```

### Excel Spreadsheets (XLSX)

```bash
# Simple extraction
curl -X POST -F "file=@spreadsheet.xlsx" http://localhost:9999/extract

# Summarization
curl -X POST -F "file=@spreadsheet.xlsx" http://localhost:9999/summary
```

### Images (with OCR)

```bash
# OCR extraction
curl -X POST -F "file=@image.jpg" http://localhost:9999/extract

# OCR summarization
curl -X POST -F "file=@image.png" http://localhost:9999/summary
```

### Audio Files (with Whisper)

```bash
# Audio transcription
curl -X POST -F "file=@audio.mp3" http://localhost:9999/extract

# Transcription and summarization
curl -X POST -F "file=@audio.m4a" http://localhost:9999/summary
```

## Integration with Other Tools

### Python with Requests

```python
import requests

# Extraction example
def extract_from_file(file_path):
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post('http://localhost:9999/extract', files=files)
    return response.text

# Summarization example
def summarize_url(url):
    data = {'url': url}
    response = requests.post('http://localhost:9999/summary', data=data)
    return response.text

# Usage examples
text = extract_from_file('document.pdf')
summary = summarize_url('https://example.com/article')
```

### Shell Script

```bash
#!/bin/bash

# Function to summarize a directory of PDFs
summarize_pdfs() {
    dir=$1
    output_dir=$2
    
    mkdir -p "$output_dir"
    
    for pdf in "$dir"/*.pdf; do
        filename=$(basename "$pdf")
        echo "Processing $filename..."
        
        summary=$(curl -s -X POST -F "file=@$pdf" http://localhost:9999/summary)
        
        echo "$summary" > "$output_dir/${filename%.pdf}_summary.txt"
        echo "Summary saved to $output_dir/${filename%.pdf}_summary.txt"
    done
}

# Usage: ./script.sh pdfs_directory output_directory
summarize_pdfs "$1" "$2"
```

## Tips and Best Practices

1. **Processing Large Documents**:
   - Tiko automatically divides large documents into chunks with its adaptive algorithm
   - The system uses a recursive approach to process large documents:
     - Divides the text into chunks based on `chunk_word_threshold` (default: 80,000 words)
     - Summarizes each chunk separately
     - Combines the partial summaries into a single text
     - Applies a final summarization step using the refiner model (when configured)
   - For extensive documents, the system automatically adjusts chunk size if it encounters errors
   - Relevant settings in `config.json`:
     ```json
     "summarizer": {
       "chunk_word_threshold": 80000
     },
     "llm": {
       "providers": {
         "litellm": {
           "model": "gemini-2.0-flash",
           "model_refiner": "gpt-4.1-mini"
         }
       }
     }
     ```

2. **Model Selection**:
   - Use smaller/faster models for simple documents
   - Reserve more advanced models for complex documents

3. **Prompt Customization**:
   - Edit the `system_prompt` in `config.json` to adjust the summarization style

4. **Performance**:
   - For high demand, consider using LiteLLM as middleware to manage requests
   - Adjust the `chunk_size` to optimize processing of large documents