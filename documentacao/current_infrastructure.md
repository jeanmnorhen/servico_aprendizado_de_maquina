# Arquitetura do Sistema de Aprendizado de Máquina

Este documento descreve a arquitetura do sistema de aprendizado de máquina, seus componentes e como eles interagem.

## Visão Geral

O sistema é uma arquitetura baseada em microserviços, orquestrada com Docker Compose. Ele é projetado para fornecer uma API para tarefas de IA, como geração de texto e imagem, e para processar tarefas de forma assíncrona usando workers Celery.

## Componentes

O sistema é composto pelos seguintes serviços:

-   **`unified_ai_api`**: Um serviço FastAPI que expõe a API principal para o mundo exterior. Ele lida com a autenticação, validação de entrada e delega tarefas para os workers Celery ou para os clientes de modelo de IA.
-   **`unified_ai_text_worker`**: Um worker Celery que processa tarefas de geração de texto. Ele usa o Ollama para executar modelos de linguagem como o Gemma.
-   **`unified_ai_vision_worker`**: Um worker Celery que processa tarefas de análise de imagem.
-   **`unified_ai_celery_beat`**: Um agendador Celery que pode ser usado para enfileirar tarefas periódicas.
-   **`ollama`**: Um serviço que expõe a API do Ollama, permitindo a execução de modelos de linguagem de código aberto.
-   **`redis`**: Um broker de mensagens para o Celery e um cache para o sistema.

## Fluxo de Dados

1.  O frontend faz uma requisição para a API `unified_ai_api`.
2.  A API `unified_ai_api` valida a requisição e a enfileira como uma tarefa no Redis.
3.  Um dos workers Celery (`unified_ai_text_worker` ou `unified_ai_vision_worker`) consome a tarefa da fila.
4.  O worker executa a tarefa, que pode envolver a chamada de um modelo de IA através do serviço `ollama` ou da API do Gemini.
5.  O resultado da tarefa é armazenado no Redis.
6.  A API `unified_ai_api` pode ser consultada para obter o status e o resultado da tarefa.

## Tecnologias

-   **Backend**: Python, FastAPI, Celery, SQLAlchemy
-   **Frontend**: Next.js, React, Tailwind CSS
-   **IA**: Ollama, Google Gemini
-   **Infraestrutura**: Docker, Docker Compose, Redis
-   **Banco de Dados**: PostgreSQL (via Supabase)

## Cobertura de Testes

O sistema possui os seguintes conjuntos de testes:

-   `tests/test_gemini_integration.py`: Testa a integração com a API do Gemini.
-   `tests/test_main.py`: Testa os endpoints da API.
-   `tests/test_text_worker.py`: Testa o worker de texto.
