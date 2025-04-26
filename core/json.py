#!/usr/bin/env python3
"""
json.py

Módulo para classificação ontológica dos documentos jurídicos.
Contém a função classify_document que analisa o conteúdo textual e retorna:
  - 'decision' se o texto contiver termos como "sentença" ou "decisão"
  - 'peticao' se o texto contiver o termo "petição"
  - 'generic' caso contrário.
"""

def generate_json(llm, text, graph_type):
    """Gera o JSON ontológico utilizando few-shot templates para orientar a LLM.
    Lê todos os arquivos que começam com 'fewshot_ontology_' do diretório 'schemas' e concatena
    seus conteúdos. Em seguida, envia uma mensagem de sistema contendo esses modelos e instruções,
    seguida por uma mensagem de usuário com o texto a ser analisado.
    Retorna o objeto JSON gerado pela LLM.
    """
    import os
    templates = []
    schemas_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'schemas'))
    for file in os.listdir(schemas_dir):
        if file.startswith('fewshot_ontology_') and file.endswith('.json'):
            try:
                with open(os.path.join(schemas_dir, file), 'r', encoding='utf-8') as f:
                    templates.append(f.read())
            except Exception as e:
                print(f'Error reading {file}: {e}')
    templates_str = "\n--- TEMPLATES ---\n".join(templates)

    messages = [
        {"role": "system", "content": (
            "You are an assistant specialized in legal document analysis. Below are some ontology models (few-shot) that should be adopted according to the nature of the document.\n "
            "IMPORTANT - follow these rules absolutely:\n"
            "1. You must adopt only one of the models I will pass below, choosing the most appropriate:\n"
            "- If the text resembles a contract more, adopt the fewshot_ontology_contrato.json model.\n"
            "- If the text resembles a judicial decision more, adopt the fewshot_ontology_decisao.json model.\n"
            "- If the text resembles a law or regulation more, adopt the fewshot_ontology_leis_normas.json model.\n"
            "- If the text resembles a study or legal opinion more, adopt the fewshot_ontology_parecer.json model.\n"
            "- If the text resembles a petition more, adopt the fewshot_ontology_peticao.json model.\n"
            "- If the text does not resemble any of the above more, adopt the fewshot_ontology_geral.json model.\n"
            "2. Do not mix models. If you choose one model, do not include fields from other models.\n"
            "3. Do not create or invent new fields that are not in the chosen model.\n"
            "4. Do not fill fields with information that is not in the document.\n"
            "5. Do not invent doctrines, jurisprudence, or citations if they are not in the document. If there are no doctrines, jurisprudence, or citations, simply do not return these fields in the json.\n"
            "6. IMPORTANT: Always fill in the content using the same language as the input document. If the document is in Portuguese, the JSON content must be in Portuguese. If the document is in English, the JSON content must be in English. The structure names (keys) remain the same, but the values should be in the document's original language.\n"
            "Below are the models:\n\n" + templates_str
        )},
        {"role": "user", "content": (
            "Using the model above that best fits the following text, and strictly adhering to the previously defined rules, analyze the following text and return only a standardized JSON object according to the model that best fits the document. "
            "Do not include fields that cannot be extracted.\n\nText:\n" + text
        )}
    ]

    headers = {'Content-Type': 'application/json'}
    if llm.api_key:
        headers['Authorization'] = f"Bearer {llm.api_key}"

    body = {
        'model': llm.model,
        'messages': messages,
        'temperature': llm.temperature,
        'max_tokens': llm.max_tokens
    }

    try:
        import requests, json
        resp = requests.post(llm.url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()
        choices = data.get('choices', [])
        if not choices:
            return None
        first = choices[0]
        msg = first.get('message')
        if isinstance(msg, dict) and 'content' in msg:
            content = msg['content'].strip()
        else:
            content = first.get('text', '').strip()
        try:
            return json.loads(content)
        except Exception as ex:
            print(f'Failed to parse response as JSON: {ex}')
            return content
    except Exception as e:
        print(f'Error calling LLM to generate JSON with templates: {e}')
        return None

if __name__ == '__main__':
    print('Test of json.py module')