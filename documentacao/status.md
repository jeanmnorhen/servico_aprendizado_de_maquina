# Estado Atual do Projeto

A refatoração principal do serviço foi concluída. O projeto agora funciona como um backend de IA flexível, seguindo os princípios da Clean Architecture e focado em fornecer acesso a múltiplos modelos de linguagem.

### Funcionalidades Implementadas

*   **API Unificada:** Um único endpoint (`/api/ai/generate-text`) serve como gateway para geração de texto.
*   **Seleção de Modelos:** A API aceita um parâmetro `model` que permite ao cliente escolher dinamicamente entre o Gemini ou qualquer modelo configurado no Ollama (ex: `codellama`, `gemma`).
*   **Persistência de Conversas:** Cada interação (pergunta e resposta) é automaticamente salva em um banco de dados Postgres (Supabase) e associada a um `session_id` para rastreamento.
*   **Arquitetura Limpa:** O código é organizado nas camadas de Domínio, Aplicação, Apresentação e Infraestrutura, promovendo baixo acoplamento e alta coesão.
*   **Ambiente Dockerizado:** Todos os serviços (API, Ollama, Redis, Celery) são gerenciados via `docker-compose` para um ambiente de desenvolvimento consistente.
*   **Túnel para Desenvolvimento:** Integração com Ngrok para expor a API local a um endereço público, facilitando o desenvolvimento de frontends.
*   **Interface de Teste:** Um arquivo `test_interface.html` permite a interação direta com a API para testes rápidos.

### Fluxo de Dados (Geração de Texto)

1.  Um cliente (ex: `test_interface.html`) envia uma requisição `POST` para `/api/ai/generate-text` com um `prompt` e um `model`.
2.  O `GenerateTextUseCase` na camada de aplicação é invocado.
3.  Ele solicita à `ModelFactory` o cliente de IA correto (`ITextGenerator`) com base no nome do modelo.
4.  O cliente selecionado (ex: `GeminiClient` ou `OllamaClient`) envia o prompt para a respectiva API de IA.
5.  Após receber a resposta da IA, o caso de uso cria um objeto `ChatHistory`.
6.  O `PostgresChatRepository` é usado para salvar o objeto `ChatHistory` no banco de dados.
7.  A resposta final e o `session_id` são retornados ao cliente.