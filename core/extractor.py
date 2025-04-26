# core/extractor.py
"""
Enhanced extractor module for Tiko application.
Provides a multi-strategy approach to extract text from various sources:
1. Uses Tika primary endpoints for standard document formats
2. Falls back to rmeta endpoint for more detailed extraction
3. As a last resort, parses HTML directly with BeautifulSoup
"""
import requests
import os
import logging

# Get the logger
logger = logging.getLogger("tiko")

class Extractor:
    def __init__(self, config):
        # Tika configuration
        self.tika_url = config['tika']['url']
        self.ocr_language = config['tika'].get('ocr_language', 'eng')
        # Whisper configuration
        whisper_cfg = config.get('whisper', {})
        self.whisper_enabled = whisper_cfg.get('enabled', False)
        self.whisper_provider = whisper_cfg.get('provider')
        self.whisper_language = whisper_cfg.get('language')
        self.whisper_model = None
        if self.whisper_enabled and self.whisper_provider == 'local':
            try:
                import whisper
                self.whisper_model = whisper.load_model(whisper_cfg.get('model', 'small'))
            except ImportError:
                logger.warning("Whisper library not installed; local transcription disabled.")
            except Exception as e:
                logger.error(f"Error loading Whisper model: {e}", exc_info=True)

    def extract_text_from_file(self, file_path):
        """Extract text from a file using various strategies."""
        file_name, file_extension = os.path.splitext(file_path)
        
        # For URLs without file extension or with generic temp filename, 
        # attempt to detect content type first
        if not file_extension or file_extension.lower() == '.tmp' or 'url_content_' in os.path.basename(file_path):
            logger.info(f"Detected URL content file: {file_path}, attempting content type detection")
            return self._extract_from_unknown_type(file_path)
            
        # Handle files by known extension
        elif file_extension.lower() in ['.html', '.htm', '.shtml', '.ghtml', '.xhtml']:
            return self._process_html_content(file_path)
        elif file_extension.lower() in ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.md', '.txt', '.rtf', '.odt']:
            return self._extract_text_with_tika(file_path)
        elif file_extension.lower() in ['.jpeg', '.jpg', '.png', '.gif', '.tiff', '.tif', '.bmp']:
            return self._extract_text_with_tika_ocr(file_path)
        elif file_extension.lower() in ['.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg', '.opus']:
            return self._extract_text_with_whisper(file_path)
        else:
            # Try generic extraction for unknown file types
            logger.info(f"Unknown file type: {file_extension}, trying generic extraction")
            return self._extract_from_unknown_type(file_path)
    
    def _extract_from_unknown_type(self, file_path):
        """Extract text from a file with unknown type using multiple strategies."""
        # Try to detect if it's HTML by content inspection
        try:
            with open(file_path, 'rb') as f:
                header = f.read(1024).lower()
                # Check if it looks like HTML
                if (b'<!doctype html>' in header or b'<html' in header or 
                    b'<head' in header or b'<body' in header):
                    logger.info(f"Content appears to be HTML based on inspection")
                    return self._process_html_content(file_path)
        except Exception as e:
            logger.error(f"Error trying to detect content type: {e}")
        
        # Try extraction methods in sequence
        logger.info(f"Trying multiple extraction methods in sequence")
        
        # Try Tika extraction first
        text = self._extract_text_with_tika(file_path)
        if text and len(text.strip()) >= 100:
            return text
            
        # Try rmeta next
        text = self._extract_text_with_rmeta(file_path)
        if text and len(text.strip()) >= 100:
            return text
            
        # As a last resort, try direct HTML parsing (handles many web content formats)
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            if b'<html' in content or b'<body' in content:
                text = self._extract_text_from_html_directly(file_path)
                if text and len(text.strip()) > 100:
                    return text
        except Exception as e:
            logger.error(f"Error trying direct HTML parsing: {e}")
        
        # Return a message if all extraction methods failed
        return "Unsupported file format"
            
    def _process_html_content(self, file_path):
        """Process HTML content with multiple fallback strategies"""
        # For HTML, we try multiple extraction methods until one succeeds
        text = self._extract_text_with_tika_main(file_path)
        if not text or len(text.strip()) < 100:  # If text is too short, try fallbacks
            logger.info(f"Initial HTML extraction failed or produced minimal text, trying rmeta endpoint")
            text = self._extract_text_with_rmeta(file_path)
        
        if not text or len(text.strip()) < 100:
            logger.info(f"rmeta extraction failed or produced minimal text, trying direct HTML parsing")
            text = self._extract_text_from_html_directly(file_path)
            
        return text

    def _extract_text_with_tika(self, file_path):
        """Extract plain text with Tika. Fallback to /tika/main if initial extraction is empty."""
        try:
            url_primary = self.tika_url.rstrip('/') + '/tika'
            with open(file_path, 'rb') as f:
                resp = requests.put(url_primary, headers={'Accept': 'text/plain'}, data=f)
            resp.raise_for_status()
            text = resp.text or ''
            if not text.strip():
                # Fallback endpoint
                url_fallback = self.tika_url.rstrip('/') + '/tika/main'
                with open(file_path, 'rb') as f2:
                    resp2 = requests.put(url_fallback, headers={'Accept': 'text/plain'}, data=f2)
                resp2.raise_for_status()
                return resp2.text
            return text
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to Tika: {e}", exc_info=True)
            return None

    def _extract_text_with_tika_main(self, file_path):
        """Extract text using Tika's /tika/main endpoint."""
        try:
            url = self.tika_url.rstrip('/') + '/tika/main'
            with open(file_path, 'rb') as f:
                resp = requests.put(url, headers={'Accept': 'text/plain'}, data=f)
            resp.raise_for_status()
            return resp.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to Tika (main endpoint): {e}", exc_info=True)
            return None

    def _extract_text_with_tika_ocr(self, file_path):
        """Extract text from image using Tika OCR."""
        try:
            base = self.tika_url.rstrip('/')
            query = f'?TesseractOCRConfig.language={self.ocr_language}'
            url = f"{base}/tika{query}"
            with open(file_path, 'rb') as f:
                resp = requests.put(url, headers={'Accept': 'text/plain'}, data=f)
            resp.raise_for_status()
            return resp.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to Tika (OCR): {e}", exc_info=True)
            return None

    def _extract_text_with_whisper(self, file_path):
        """Extract text from audio using Whisper."""
        if not (self.whisper_enabled and self.whisper_model):
            logger.warning("Whisper transcription not available")
            return "Whisper transcription not available"
        try:
            # Transcribe audio locally
            result = self.whisper_model.transcribe(file_path, language=self.whisper_language)
            return result.get('text', '')
        except Exception as e:
            logger.error(f"Error during Whisper transcription: {e}", exc_info=True)
            return None
        finally:
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception as e:
                logger.warning(f"Error during CUDA cache emptying: {e}")
                
    def _extract_text_with_rmeta(self, file_path):
        """Extract text using Tika's /rmeta endpoint, which provides more detailed metadata."""
        try:
            url = self.tika_url.rstrip('/') + '/rmeta'
            with open(file_path, 'rb') as f:
                resp = requests.put(url, headers={'Accept': 'application/json'}, data=f)
            resp.raise_for_status()
            
            # Parse the JSON response
            import json
            data = json.loads(resp.text)
            
            if data and isinstance(data, list) and len(data) > 0:
                # Extract content fields that might contain text
                text_parts = []
                
                # Check for content field
                if 'X-TIKA:content' in data[0]:
                    text_parts.append(data[0]['X-TIKA:content'])
                    
                # Check for other content fields like title, description
                for field in ['title', 'description', 'og:description', 'dc:title', 'Content-Type']:
                    if field in data[0]:
                        text_parts.append(f"{field}: {data[0][field]}")
                
                return "\n\n".join(text_parts)
            return None
        except Exception as e:
            logger.error(f"Error extracting text with rmeta endpoint: {e}", exc_info=True)
            return None
            
    def _extract_text_from_html_directly(self, file_path):
        """Extract text directly from HTML using BeautifulSoup when Tika fails."""
        try:
            # Import necessary libraries
            from bs4 import BeautifulSoup
            
            # Read the HTML file
            with open(file_path, 'rb') as f:
                content = f.read()
                
            # Try different encodings if needed
            encodings = ['utf-8', 'latin-1', 'ISO-8859-1', 'windows-1252']
            html_content = None
            
            for encoding in encodings:
                try:
                    html_content = content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
                    
            if not html_content:
                logger.warning(f"Could not decode HTML content with any known encoding")
                return None
                
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove non-content elements
            for element in soup(['script', 'style', 'header', 'footer', 'nav', 'aside']):
                element.decompose()
                
            # Smart extraction strategy - try to identify content areas
            content_elements = []
            
            # Step 1: Try to find main content containers by common selectors
            selectors = [
                'article', 'main', '[role="main"]', '.article-content', '.post-content', 
                '.story-content', '.entry-content', '.news-content', '.story-body', 
                '.main-content', '.materia-corpo', '.post-body', '.conteudo',
                '#content', '.content', '[itemprop="articleBody"]'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    content_elements.extend(elements)
                    break
            
            # Step 2: If no luck with selectors, try common structural patterns
            if not content_elements:
                for tag in ['article', 'main', 'section', 'div']:
                    for elem in soup.find_all(tag):
                        # Check if element contains multiple paragraphs (likely content)
                        paragraphs = elem.find_all('p')
                        if len(paragraphs) >= 3:
                            content_elements.append(elem)
            
            # Step 3: Extract text from identified content elements
            if content_elements:
                all_paragraphs = []
                for element in content_elements:
                    paragraphs = element.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    all_paragraphs.extend(paragraphs)
                
                if all_paragraphs:
                    text = "\n".join([p.get_text().strip() for p in all_paragraphs if p.get_text().strip()])
                    if text and len(text) > 100:
                        return text
            
            # Fallback: Extract from all paragraphs if no content container found
            all_paragraphs = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if all_paragraphs and len(all_paragraphs) > 3:
                text = "\n".join([p.get_text().strip() for p in all_paragraphs if p.get_text().strip()])
                if text and len(text) > 100:
                    return text
            
            # Last resort: extract all text
            text = soup.get_text(separator="\n")
            
            # Clean up the text
            lines = (line.strip() for line in text.splitlines())
            lines = (line for line in lines if line)  # Remove empty lines
            text = "\n".join(lines)
            
            return text
            
        except ImportError:
            logger.warning("BeautifulSoup is not installed, cannot parse HTML directly")
            return "ERROR: BeautifulSoup is required for direct HTML parsing. Install with 'pip install beautifulsoup4'."
        except Exception as e:
            logger.error(f"Error parsing HTML directly: {e}", exc_info=True)
            return None
            
