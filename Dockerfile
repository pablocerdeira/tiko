FROM python:3.10-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivos de dependências
COPY requirements.txt .

# Instalar dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o código da aplicação
COPY ./app .

# Criar diretórios necessários
RUN mkdir -p logs uploads tmp

# Expor a porta usada pelo servidor
EXPOSE 9997

# Definir variáveis de ambiente
ENV PYTHONUNBUFFERED=1

# Comando para iniciar o servidor
CMD ["python", "-m", "api.server"]
