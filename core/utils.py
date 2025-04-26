#!/usr/bin/env python3
"""
Utilities module for Tiko.
Provides general utility functions used across the application.
"""
import logging
import json
import datetime

# Get the logger
logger = logging.getLogger("tiko")

def fix_encoding_recursive(data):
    """Applies fix_encoding recursively to strings inside dicts and lists."""
    if isinstance(data, str):
        return fix_encoding(data)
    elif isinstance(data, dict):
        return {key: fix_encoding_recursive(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [fix_encoding_recursive(item) for item in data]
    else:
        return data

def fix_encoding(text):
    """Attempt to fix mis-encoded text by re-encoding from latin1 to utf-8 if the result seems improved."""
    try:
        import ftfy
        return ftfy.fix_text(text)
    except ImportError:
        # Fallback method if ftfy is not available
        try:
            fixed = text.encode('latin1').decode('utf-8')
            non_ascii_original = sum(1 for c in text if ord(c) > 127)
            non_ascii_fixed = sum(1 for c in fixed if ord(c) > 127)
            if non_ascii_fixed < non_ascii_original:
                return fixed
            else:
                return text
        except Exception as e:
            logger.warning(f'Encoding fix failed: {e}')
            return text

def detect_encoding(content):
    """Detect encoding of content using chardet."""
    try:
        import chardet
        result = chardet.detect(content)
        return result['encoding']
    except ImportError:
        logger.warning("chardet library not available; defaulting to utf-8")
        return 'utf-8'
    except Exception as e:
        logger.warning(f"Error detecting encoding: {e}")
        return 'utf-8'
        
class JSONFormatter(logging.Formatter):
    """JSON formatter for logging that structures log entries as JSON objects."""
    def format(self, record):
        """Format log record as JSON."""
        log_record = {
            "timestamp": datetime.datetime.now().isoformat(),
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage()
        }

        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }

        return json.dumps(log_record)