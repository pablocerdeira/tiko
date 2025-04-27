# Dockerized Tiko

Este documento explica como executar o Tiko em containers Docker.

## Pré-requisitos

- Docker
- Docker Compose

## Estrutura dos arquivos

- **Dockerfile**: Construção da imagem Docker do Tiko
- **docker-compose.yml**: Configuração para orquestrar os containers do Tiko e Apache Tika
- **.dockerignore**: Lista de arquivos/diretórios que não serão incluídos na imagem

## Como executar

### 1. Construir e iniciar os containers

```bash
docker-compose up -d
```

Este comando constrói a imagem do Tiko se necessário e inicia dois containers:
- **tika**: Apache Tika na porta 9998
- **tiko**: Aplicação Tiko na porta 9997

### 2. Verificar status

```bash
docker-compose ps
```

### 3. Verificar logs

```bash
docker-compose logs -f
```

Para verificar logs de um serviço específico:

```bash
docker-compose logs -f tiko
```

### 4. Testar a API

```bash
curl "http://localhost:9997/health?token=DevInternal92461724618920"
```

Deve retornar algo como:
```json
{"status": "ok", "version": "0.5.1"}
```

### 5. Parar os containers

```bash
docker-compose down
```

## Volumes e persistência

O Docker Compose monta vários volumes para garantir a persistência de dados e configurações:

- **config.json**: Configuração principal
- **tokens.json**: Tokens de autenticação
- **logs/**: Pasta de logs
- **uploads/**: Pasta de uploads temporários

## Personalização

### Modificar a configuração

Edite o arquivo `config.json` local e reinicie o serviço:

```bash
docker-compose restart tiko
```

### Modificar os tokens

Edite o arquivo `tokens.json` local e reinicie o serviço:

```bash
docker-compose restart tiko
```

## Considerações para produção

Para ambientes de produção, considere:

1. Configurar um servidor de proxy reverso (NGINX/Traefik)
2. Configurar TLS/SSL para tráfego seguro
3. Implementar limites de recursos no Docker Compose
4. Configurar monitoramento e alerta
5. Utilizar um serviço de orquestração como Kubernetes para alta disponibilidade