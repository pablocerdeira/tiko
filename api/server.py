from flask import Flask, request, jsonify
import os
import json
import logging
import datetime
import sys
import threading
import time
import functools
from core.summarizer import Summarizer
from core.web_extractor import get_input_file
from core.utils import fix_encoding_recursive, JSONFormatter

# Set up the logger
logger = logging.getLogger("tiko")
logger.setLevel(logging.INFO)

# Create a handler for console output
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(JSONFormatter())
logger.addHandler(console_handler)

# Create a file handler if logs directory exists
logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs'))
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

file_handler = logging.FileHandler(os.path.join(logs_dir, f"tiko_{datetime.datetime.now().strftime('%Y%m%d')}.log"))
file_handler.setFormatter(JSONFormatter())
logger.addHandler(file_handler)

# Load tokens from tokens.json
tokens_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tokens.json'))
tokens = {}

def load_tokens():
    """Load tokens from tokens.json file"""
    global tokens
    try:
        if os.path.exists(tokens_path):
            with open(tokens_path, 'r') as f:
                tokens_data = json.load(f)
                tokens = tokens_data.get('tokens', {})
                logger.info(f"Loaded {len(tokens)} tokens from tokens.json")
        else:
            logger.warning(f"Tokens file not found at {tokens_path}")
    except Exception as e:
        logger.error(f"Error loading tokens: {e}", exc_info=True)

# Load tokens initially
load_tokens()

# Set up token file monitoring
tokens_mtime = os.path.getmtime(tokens_path) if os.path.exists(tokens_path) else 0
tokens_lock = threading.Lock()

def monitor_tokens():
    """Monitor tokens.json for changes and reload when needed"""
    global tokens, tokens_mtime
    while True:
        try:
            time.sleep(5)  # Check every 5 seconds
            if os.path.exists(tokens_path):
                current_mtime = os.path.getmtime(tokens_path)
                if current_mtime != tokens_mtime:
                    with tokens_lock:
                        load_tokens()
                        tokens_mtime = current_mtime
                        logger.info('Tokens updated')
        except Exception as e:
            logger.error(f'Error monitoring tokens: {e}', exc_info=True)
            time.sleep(5)

tokens_thread = threading.Thread(target=monitor_tokens, daemon=True)
tokens_thread.start()

def require_token(f):
    """Decorator to require token authentication"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if auth is enabled in config
        auth_enabled = config.get('auth', {}).get('enabled', True)
        if not auth_enabled:
            return f(*args, **kwargs)
            
        # Check if this endpoint is excluded from authentication
        endpoint = request.path
        exclude_endpoints = config.get('auth', {}).get('exclude_endpoints', [])
        if endpoint in exclude_endpoints:
            return f(*args, **kwargs)
            
        token = request.args.get('token')
        
        if not token:
            logger.warning(f"Unauthorized access attempt: No token provided - {request.method} {request.path}")
            return jsonify({"error": "Unauthorized - Token required"}), 401
        
        if token not in tokens:
            logger.warning(f"Unauthorized access attempt: Invalid token - {request.method} {request.path}")
            return jsonify({"error": "Unauthorized - Invalid token"}), 401
            
        token_info = tokens[token]
        if not token_info.get('active', False):
            logger.warning(f"Unauthorized access attempt: Inactive token - {request.method} {request.path}")
            return jsonify({"error": "Unauthorized - Token inactive"}), 401
            
        # Log token usage
        logger.info(f"Token used: {token_info.get('name', 'Unknown')} - {request.method} {request.path}")
        return f(*args, **kwargs)
    return decorated_function

# Initialize the Flask app
app = Flask(__name__)

# Add request logging middleware
@app.before_request
def log_request_info():
    logger.info(f"Request: {request.method} {request.path} - Headers: {dict(request.headers)}")

@app.after_request
def log_response_info(response):
    logger.info(f"Response: {response.status} - Size: {response.content_length}")
    return response

# Load configuration
config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.json'))
with open(config_path, 'r') as f:
    config = json.load(f)

summarizer = Summarizer(config)

# Set up configuration monitoring
config_mtime = os.path.getmtime(config_path)
config_lock = threading.Lock()

def monitor_config():
    global config, summarizer, config_mtime
    while True:
        try:
            time.sleep(1)  # Check every second
            current_mtime = os.path.getmtime(config_path)
            if current_mtime != config_mtime:
                with config_lock:
                    with open(config_path, 'r') as f:
                        new_config = json.load(f)
                    config = new_config
                    summarizer = Summarizer(config)
                    config_mtime = current_mtime
                    logger.info('Configuration updated')
        except Exception as e:
            logger.error(f'Error monitoring config: {e}', exc_info=True)
            time.sleep(1)

config_thread = threading.Thread(target=monitor_config, daemon=True)
config_thread.start()

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/extract', methods=['POST'])
@require_token
def extract():
    file_path = get_input_file(request, app.config['UPLOAD_FOLDER'])
    if not file_path:
        return 'No file or URL provided', 400

    try:
        text = summarizer.extractor.extract_text_from_file(file_path)
        text = fix_encoding_recursive(text)
        os.remove(file_path)
        if not text:
            return 'Failed to extract text', 500
        return text, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        logger.error(f"Error during extraction: {str(e)}", exc_info=True)
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        return f"Internal server error: {str(e)}", 500

@app.route('/summary', methods=['POST'])
@require_token
def summary():
    logger.info(f"Summary request received: {request.method} {request.path}")
    file_path = get_input_file(request, app.config['UPLOAD_FOLDER'])
    if not file_path:
        return 'No file or URL provided', 400

    try:
        # Use the summarizer to get the full summary
        summary_text = summarizer.summarize_file(file_path)
        # Clean up the file after processing
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        
        if not summary_text:
            return 'Failed to generate summary', 500
            
        # Return the summary with appropriate headers
        return summary_text, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        logger.error(f"Error during summarization: {str(e)}", exc_info=True)
        # Clean up the file if it exists
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        return f"Internal server error: {str(e)}", 500

@app.route('/health', methods=['GET'])
@require_token
def health():
    return jsonify({
        'status': 'ok',
        'version': config.get('version', '0.5.1')
    })

@app.route('/json', methods=['POST'])
@require_token
def json_response():
    # Get file from 'file' field or via URL
    file_path = get_input_file(request, app.config['UPLOAD_FOLDER'])
    if not file_path:
        return 'No file or URL provided', 400

    try:
        # Extract text from file
        text = summarizer.extractor.extract_text_from_file(file_path)
        if not text:
            os.remove(file_path)
            return 'Could not extract text from file for JSON generation.', 400

        # Generate JSON object using few-shot templates
        from core.json import generate_json
        # Use the type parameter from request args if provided
        graph_type = request.args.get('type', '')
        result = generate_json(summarizer.llm, text, graph_type)
        
        if result is None:
            os.remove(file_path)
            return 'Error generating JSON from extracted text.', 500

        # Apply recursive encoding fix if applicable
        result = fix_encoding_recursive(result) if result else result

        os.remove(file_path)

        if isinstance(result, dict):
            response_json = json.dumps(result, indent=2, ensure_ascii=False)
            return response_json, 200, {'Content-Type': 'application/json; charset=utf-8'}
        else:
            return result, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        logger.error(f"Error during JSON generation: {str(e)}", exc_info=True)
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        return f"Internal server error: {str(e)}", 500

if __name__ == '__main__':
    srv = config.get('server', {})
    host = srv.get('host', '0.0.0.0')
    port = srv.get('port', 9999)
    debug = srv.get('debug', False)
    app.run(host=host, port=port, debug=debug)