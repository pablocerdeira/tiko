# core/llm.py
"""
core/llm.py
Provides a generic LLM interface based on HTTP JSON APIs.
Configuration in config.json under 'llm.providers'.
Supports chat-style endpoints returning choices[].message.content or completion-style with choices[].text.
"""
import requests

class LLM:
    def _read_template(self, template_filename):
        import os
        try:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'schemas'))
            template_path = os.path.join(base_dir, template_filename)
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f'Error reading template {template_filename}: {e}')
            return ''
        
    def __init__(self, config):
        llm_cfg = config.get('llm', {})
        self.provider = llm_cfg.get('provider')
        providers = llm_cfg.get('providers', {})
        cfg = providers.get(self.provider, {})
        # API endpoint URL
        self.url = cfg.get('url')
        if not self.url:
            self.url = cfg.get('base_url')
        # Credentials: prefer config, fallback to env.<PROVIDER>_API_KEY
        raw_key = cfg.get('api_key')
        if raw_key:
            self.api_key = raw_key
        else:
            import os
            env_var = f"{self.provider.upper()}_API_KEY"
            self.api_key = os.getenv(env_var)
        # Model and prompts
        self.model = cfg.get('model')
        self.system_prompt = cfg.get('system_prompt', '')
        # Tuning parameters
        self.temperature = cfg.get('temperature', llm_cfg.get('temperature', 0.7))
        self.max_tokens = cfg.get('max_tokens', llm_cfg.get('max_tokens', 150))
        self.context_window_fallback = cfg.get('context_window_fallback', None)

    def summarize(self, text):
        # This method uses the system prompt defined in config.json for summary generation.
        if not self.url:
            print(f"LLM provider '{self.provider}' missing URL in configuration.")
            return None

        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f"Bearer {self.api_key}"
            
        # Add language instruction to the system prompt
        language_instruction = "IMPORTANT: Always respond in the same language as the input text. Maintain the original language of the document in your response."
        enhanced_system_prompt = f"{self.system_prompt}\n\n{language_instruction}"
        
        body = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': enhanced_system_prompt},
                {'role': 'user', 'content': text}
            ],
            'temperature': self.temperature,
            'max_tokens': self.max_tokens
        }

        try:
            resp = requests.post(self.url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
            choices = data.get('choices', [])
            if not choices:
                return None
            first = choices[0]
            msg = first.get('message')
            if isinstance(msg, dict) and 'content' in msg:
                return msg['content'].strip()
            text_out = first.get('text')
            if isinstance(text_out, str):
                return text_out.strip()
            return None
        except Exception as e:
            print(f"Error calling LLM provider '{self.provider}': {e}")
            return None