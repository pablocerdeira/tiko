# api/server.py
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import json
from core.summarizer import Summarizer

def fix_encoding_recursive(data):
    # Applies fix_encoding recursively to strings inside dicts and lists
    if isinstance(data, str):
        return fix_encoding(data)
    elif isinstance(data, dict):
        return {key: fix_encoding_recursive(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [fix_encoding_recursive(item) for item in data]
    else:
        return data
import chardet

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
            print(f'Encoding fix failed: {e}')
            return text
import threading
import time
app = Flask(__name__)

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
                    print('Configuration updated')
        except Exception as e:
            print(f'Error monitoring config: {e}')
            time.sleep(1)

config_thread = threading.Thread(target=monitor_config, daemon=True)
config_thread.start()

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
import requests

def get_input_file(req):
    """Gets the input file from the request. If there is a 'url' field in the form and it's a URL, downloads the content and saves it to a temporary file. Otherwise, uses request.files['file']."""
    url = req.form.get('url', '').strip()
    if url and url.startswith(('http://', 'https://')):
        filename = url.rstrip('/').split('/')[-1] or 'downloaded_content'
        filename = secure_filename(filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"})
            r.raise_for_status()
            with open(file_path, 'wb') as f:
                f.write(r.content)
            return file_path
        except Exception as e:
            print(f"Error downloading file from URL {url}: {e}")
            return None
    elif 'file' in req.files and req.files['file'].filename:
        file_obj = req.files['file']
        filename = secure_filename(file_obj.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file_obj.save(file_path)
        return file_path
    else:
        return None

@app.route('/summary', methods=['POST'])
def summarize():
    # Get file from 'file' field or URL provided via form ('url')
    file_path = get_input_file(request)
    if not file_path:
        msg = 'No valid file or URL provided'
        return msg, 400, {'Content-Type': 'text/plain; charset=utf-8'}

    # Retrieve optional overrides
    model_override = request.args.get('model')
    api_key_override = request.args.get('api_key')
    if model_override or api_key_override:
        temp_summarizer = Summarizer(config)
        if model_override:
            temp_summarizer.llm.model = model_override
        if api_key_override:
            temp_summarizer.llm.api_key = api_key_override
        sch = temp_summarizer
    else:
        sch = summarizer

    result = sch.summarize_file(file_path)
    result = fix_encoding(result)
    os.remove(file_path)
    return result, 200, {'Content-Type': 'text/plain; charset=utf-8'}

@app.route('/extract', methods=['POST'])
def extract():
    file_path = get_input_file(request)
    if not file_path:
        msg = 'No valid file or URL provided'
        return msg, 400, {'Content-Type': 'text/plain; charset=utf-8'}

    result = summarizer.extractor.extract_text_from_file(file_path)
    if not result:
        result = 'Unable to extract text from file.'
    result = fix_encoding(result)
    os.remove(file_path)
    return result, 200, {'Content-Type': 'text/plain; charset=utf-8'}

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

@app.route('/json', methods=['POST'])
def json_response():
    # Get file from 'file' field or via URL
    file_path = get_input_file(request)
    if not file_path:
        msg = 'No valid file or URL provided'
        return msg, 400, {'Content-Type': 'text/plain; charset=utf-8'}

    # Extract text from file
    text = summarizer.extractor.extract_text_from_file(file_path)
    if not text:
        os.remove(file_path)
        msg = 'Could not extract text from file for JSON generation.'
        return msg, 400, {'Content-Type': 'text/plain; charset=utf-8'}

    # Generate JSON object using few-shot templates
    from core.json import generate_json
    try:
        # Use the type parameter from request args if provided
        graph_type = request.args.get('type', '')
        result = generate_json(summarizer.llm, text, graph_type)
        if result is None:
            os.remove(file_path)
            msg = 'Error generating JSON from extracted text.'
            return msg, 500, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        os.remove(file_path)
        msg = f'Error during JSON generation: {str(e)}'
        return msg, 500, {'Content-Type': 'text/plain; charset=utf-8'}

    # Apply recursive encoding fix if applicable
    result = fix_encoding_recursive(result) if result else result

    os.remove(file_path)

    import json
    if isinstance(result, dict):
        response_json = json.dumps(result, indent=2, ensure_ascii=False)
        return response_json, 200, {'Content-Type': 'application/json; charset=utf-8'}
    else:
        return result, 200, {'Content-Type': 'text/plain; charset=utf-8'}

@app.route('/graph', methods=['POST'])
def graph_response():
    # Get file from 'file' field or via URL
    file_path = get_input_file(request)
    if not file_path:
        msg = 'No valid file or URL provided'
        return msg, 400, {'Content-Type': 'text/plain; charset=utf-8'}

    # Extract text from file
    text = summarizer.extractor.extract_text_from_file(file_path)
    if not text:
        os.remove(file_path)
        msg = 'Could not extract text from file for graph generation.'
        return msg, 400, {'Content-Type': 'text/plain; charset=utf-8'}

    # Generate graph using GraphGenerator
    from core.graph import GraphGenerator
    try:
        # Use the type parameter from request args if provided
        graph_type = request.args.get('type', '')
        graph_generator = GraphGenerator(summarizer.llm)
        result = graph_generator.generate_graph(text, graph_type)
        if result is None:
            os.remove(file_path)
            msg = 'Error generating graph from extracted text.'
            return msg, 500, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        os.remove(file_path)
        msg = f'Error during graph generation: {str(e)}'
        return msg, 500, {'Content-Type': 'text/plain; charset=utf-8'}

    # Apply recursive encoding fix if applicable
    result = fix_encoding_recursive(result) if result else result

    os.remove(file_path)

    import json
    if isinstance(result, dict):
        response_json = json.dumps(result, indent=2, ensure_ascii=False)
        return response_json, 200, {'Content-Type': 'application/json; charset=utf-8'}
    else:
        return result, 200, {'Content-Type': 'text/plain; charset=utf-8'}

if __name__ == '__main__':
    srv = config.get('server', {})
    host = srv.get('host', '0.0.0.0')
    port = srv.get('port', 9999)
    debug = srv.get('debug', False)
    app.run(host=host, port=port, debug=debug)
