 1 # Pontos de Melhoria                                                                                                        │
│     2                                                                                                                             │
│     3 Esta lista documenta possíveis melhorias técnicas para a arquitetura e implementação atual do serviço.                      │
│     4                                                                                                                             │
│     5 *   **Refatorar `LlavaClient` (Prioridade Alta):**                                                                          │
│     6     *   **Descrição:** Atualmente, o `LlavaClient` está isolado. Ele deve ser integrado à `ModelFactory` para que a análise │
│       de imagens siga o mesmo padrão arquitetural da geração de texto.                                                            │
│     7     *   **Solução Sugerida:** Criar uma interface `IImageAnalyzer`, implementá-la no `LlavaClient` e na `ModelFactory`, e   │
│       criar um caso de uso e endpoint específicos para análise de imagem.                                                         │
│     8                                                                                                                             │
│     9 *   **Gerenciamento de Configuração (Prioridade Média):**                                                                   │
│    10     *   **Descrição:** A URL do serviço Ollama (`http://ollama:11434`) está hardcoded nos clientes. Isso dificulta a        │
│       alteração do endereço sem modificar o código.                                                                               │
│    11     *   **Solução Sugerida:** Mover a URL do Ollama para uma variável de ambiente no arquivo `.env` (ex: `OLLAMA_API_URL`)  │
│       e lê-la nos clientes.                                                                                                       │
│    12                                                                                                                             │
│    13 *   **Estratégia de Testes (Prioridade Alta):**                                                                             │
│    14     *   **Descrição:** O projeto carece de testes automatizados para as novas funcionalidades, o que é um risco para a      │
│       manutenção e evolução do código. Os testes existentes estão obsoletos.                                                      │
│    15     *   **Solução Sugerida:** Implementar uma estratégia de testes robusta, focando nas novas funcionalidades:              │
│    16         1.  **Remover Testes Obsoletos:** Excluir `tests/test_text_worker.py` e remover os testes de `catalog_intake` de    │
│       `tests/test_main.py`.                                                                                                       │
│    17         2.  **Testes Unitários para Clientes de IA:**                                                                       │
│    18             *   Criar testes para `GeminiClient`, `GeminiImageClient`, `OllamaClient`, mockando as chamadas externas às     │
│       APIs.                                                                                                                       │
│    19         3.  **Testes Unitários para `ModelFactory`:**                                                                       │
│    20             *   Garantir que a fábrica retorne o cliente correto com base no nome do modelo.                                │
│    21         4.  **Testes Unitários para Repositório:**                                                                          │
│    22             *   Testar `PostgresChatRepository`, mockando a sessão do SQLAlchemy para verificar a lógica de `add` e         │
│       `get_by_session_id`.                                                                                                        │
│    23         5.  **Testes Unitários para Casos de Uso:**                                                                         │
│    24             *   Testar `GenerateTextUseCase` e `GenerateImageUseCase`, mockando seus clientes de IA e repositórios.         │
│    25         6.  **Testes de Integração para Endpoints:**                                                                        │
│    26             *   Criar testes de integração para os novos endpoints (`/api/ai/generate-text`, `/api/ai/generate-image`),     │
│       usando o `TestClient` do FastAPI. Mockar as dependências externas (clientes de IA, repositório) para focar na integração do │
│       endpoint com o caso de uso.                                                                                                 │
│    27         7.  **Testes de Edge Cases:** Adicionar testes para cenários de erro (ex: API key inválida, modelo não encontrado,  │
│       falha na API externa, falha no banco de dados).                                                                             │
│    28                                                                                                                             │
│    29 *   **Tratamento de Erros e Logging (Prioridade Média):**                                                                   │
│    30     *   **Descrição:** O tratamento de erros atual é básico. Em um ambiente de produção, é necessário um logging mais       │
│       estruturado e detalhado.                                                                                                    │
│    31     *   **Solução Sugerida:** Integrar uma biblioteca de logging (como o `loguru`) para gerar logs estruturados em JSON.    │
│       Implementar um middleware no FastAPI para capturar exceções não tratadas e logá-las adequadamente.                          │
│    32                                                                                                                             │
│    33 *   **Segurança (Prioridade Baixa para Dev, Alta para Prod):**                                                              │
│    34     *   **Descrição:** A segurança atual se baseia em uma única chave de API estática. Para um cenário multi-usuário, isso  │
│       é insuficiente.                                                                                                             │
│    35     *   **Solução Sugerida:** Explorar mecanismos de autenticação mais avançados, como OAuth2 ou tokens JWT, caso a API     │
│       venha a ser exposta publicamente de forma mais ampla.  