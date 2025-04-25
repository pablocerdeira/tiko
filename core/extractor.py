# core/extractor.py
import requests
import os

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
                print("Whisper library not installed; local transcription disabled.")
            except Exception as e:
                print(f"Error loading Whisper model: {e}")

    def extract_text_from_file(self, file_path):
        file_name, file_extension = os.path.splitext(file_path)
        # Document types: use Tika for text extraction; for HTML use the /tika/main endpoint
        if file_extension.lower() in ['.html', '.htm']:
            return self._extract_text_with_tika_main(file_path)
        elif file_extension.lower() in ['.pdf', '.docx', '.xlsx', '.md', '.txt']:
            return self._extract_text_with_tika(file_path)
        # Images: use Tika with OCR
        elif file_extension.lower() in ['.jpeg', '.jpg', '.png', '.gif']:
            return self._extract_text_with_tika_ocr(file_path)
        # Audio: use Whisper if enabled
        elif file_extension.lower() in ['.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg', '.opus']:
            return self._extract_text_with_whisper(file_path)
        else:
            return "Unsupported file format"

    def _extract_text_with_tika(self, file_path):
        """
        Extract plain text with Tika. Fallback to /tika/main if initial extraction is empty.
        """
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
            print(f"Erro ao conectar com o Tika: {e}")
            return None

    def _extract_text_with_tika_main(self, file_path):
        """Extract plain text from HTML using Tika's /tika/main endpoint as fallback for HTML documents."""
        try:
            url_fallback = self.tika_url.rstrip('/') + '/tika/main'
            with open(file_path, 'rb') as f2:
                resp2 = requests.put(url_fallback, headers={'Accept': 'text/plain'}, data=f2)
            resp2.raise_for_status()
            return resp2.text
        except requests.exceptions.RequestException as e:
            print(f"Erro ao conectar com o Tika (Fallback HTML): {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Erro ao conectar com o Tika: {e}")
            return None

    def _extract_text_with_tika_ocr(self, file_path):
        """
        Extract text from image using Tika OCR. Fallback to /tika/main if needed.
        """
        try:
            base = self.tika_url.rstrip('/')
            query = f'?TesseractOCRConfig.language={self.ocr_language}'
            url_primary = f"{base}/tika{query}"
            with open(file_path, 'rb') as f:
                resp = requests.put(url_primary, headers={'Accept': 'text/plain'}, data=f)
            resp.raise_for_status()
            text = resp.text or ''
            if not text.strip():
                # Fallback endpoint
                url_fallback = f"{base}/tika/main{query}"
                with open(file_path, 'rb') as f2:
                    resp2 = requests.put(url_fallback, headers={'Accept': 'text/plain'}, data=f2)
                resp2.raise_for_status()
                return resp2.text
            return text
        except requests.exceptions.RequestException as e:
            print(f"Erro ao conectar com o Tika (OCR): {e}")
            return None

    def _extract_text_with_whisper(self, file_path):
        if not (self.whisper_enabled and self.whisper_model):
            return "Whisper transcription not available"
        try:
            # Transcribe audio locally
            result = self.whisper_model.transcribe(file_path, language=self.whisper_language)
            return result.get('text', '')
        except Exception as e:
            print(f"Error during Whisper transcription: {e}")
            return None
        finally:
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception as e:
                print(f"Error during CUDA cache emptying: {e}")
