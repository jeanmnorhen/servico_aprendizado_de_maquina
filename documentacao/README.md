# Serviço de Aprendizado de Máquina

Este projeto é um serviço de backend robusto que fornece uma API unificada para interagir com múltiplos modelos de linguagem grandes (LLMs). Ele é construído seguindo os princípios da Clean Architecture para garantir manutenibilidade, escalabilidade e testabilidade.

## Arquitetura

O serviço utiliza uma arquitetura em camadas para separar as responsabilidades:

*   **API (FastAPI):** A camada de apresentação, responsável por expor os endpoints HTTP. Ela recebe as requisições e as encaminha para a camada de aplicação.

*   **Application Layer:** Contém os casos de uso (`Use Cases`) que orquestram a lógica de negócio. Por exemplo, o `GenerateTextUseCase` coordena a geração de texto e sua persistência.

*   **Domain Layer:** O núcleo do sistema. Define os modelos de dados (ex: `ChatHistory`) e as interfaces (`Ports`) que estabelecem os contratos que as camadas externas devem seguir (ex: `ITextGenerator`, `IChatRepository`).

*   **Infrastructure Layer:** Contém a implementação concreta das interfaces do domínio. É aqui que as tecnologias externas são integradas:
    *   **IA Models:** Uma `ModelFactory` seleciona o cliente de IA apropriado:
        *   `GeminiClient`: Para interagir com a API do Google Gemini.
        *   `OllamaClient`: Para interagir com modelos auto-hospedados via Ollama (ex: CodeLlama, Gemma).
    *   **Persistência (Supabase/Postgres):** Um `PostgresChatRepository` usa SQLAlchemy para salvar o histórico de conversas em um banco de dados Postgres, fornecido pelo Supabase.
    *   **Task Queue (Celery/Redis):** A base para processamento assíncrono de tarefas de longa duração está presente, utilizando Celery e Redis.

*   **Desenvolvimento Local (Docker & Ngrok):**
    *   O ambiente de desenvolvimento é totalmente containerizado com `docker-compose`.
    *   O Ngrok é integrado para criar um túnel seguro para a API local, permitindo que ela seja acessada publicamente (por exemplo, por um frontend hospedado na Vercel).

## Como Executar (Localmente)

1.  **Configurar Variáveis de Ambiente:**
    *   Renomeie `.env.example` para `.env`.
    *   Preencha as variáveis do Supabase (`supabase_POSTGRES_URL`, etc.) e o `NGROK_AUTHTOKEN` com suas credenciais.

2.  **Iniciar os Serviços (Docker):**
    *   No terminal, na raiz do projeto, execute:
        ```bash
        docker-compose up --build
        ```

3.  **Acessar a Aplicação:**
    *   Aguarde os containers iniciarem. A URL pública do Ngrok será exibida nos logs do terminal.
    *   A API estará acessível localmente em [http://localhost:8000](http://localhost:8000).
    *   Uma interface de teste está disponível abrindo o arquivo `test_interface.html` no seu navegador.