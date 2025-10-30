# Pontos de Melhoria

Esta lista documenta possíveis melhorias técnicas para a arquitetura e implementação atual do serviço.

*   **Refatorar `LlavaClient` (Prioridade Alta):**
    *   **Descrição:** Atualmente, o `LlavaClient` está isolado. Ele deve ser integrado à `ModelFactory` para que a análise de imagens siga o mesmo padrão arquitetural da geração de texto.
    *   **Solução Sugerida:** Criar uma interface `IImageAnalyzer`, implementá-la no `LlavaClient` e na `ModelFactory`, e criar um caso de uso e endpoint específicos para análise de imagem.

*   **Gerenciamento de Configuração (Prioridade Média):**
    *   **Descrição:** A URL do serviço Ollama (`http://ollama:11434`) está hardcoded nos clientes. Isso dificulta a alteração do endereço sem modificar o código.
    *   **Solução Sugerida:** Mover a URL do Ollama para uma variável de ambiente no arquivo `.env` (ex: `OLLAMA_API_URL`) e lê-la nos clientes.

*   **Estratégia de Testes (Prioridade Alta):**
    *   **Descrição:** O projeto carece de testes automatizados, o que é um risco para a manutenção e evolução do código.
    *   **Solução Sugerida:** Implementar uma estratégia de testes robusta, incluindo:
        *   **Testes Unitários:** Para as regras de negócio no Domínio e na Aplicação.
        *   **Testes de Integração:** Para a camada de Infraestrutura, utilizando mocks para os serviços externos (APIs, banco de dados).

*   **Tratamento de Erros e Logging (Prioridade Média):**
    *   **Descrição:** O tratamento de erros atual é básico. Em um ambiente de produção, é necessário um logging mais estruturado e detalhado.
    *   **Solução Sugerida:** Integrar uma biblioteca de logging (como o `loguru`) para gerar logs estruturados em JSON. Implementar um middleware no FastAPI para capturar exceções não tratadas e logá-las adequadamente.

*   **Segurança (Prioridade Baixa para Dev, Alta para Prod):**
    *   **Descrição:** A segurança atual se baseia em uma única chave de API estática. Para um cenário multi-usuário, isso é insuficiente.
    *   **Solução Sugerida:** Explorar mecanismos de autenticação mais avançados, como OAuth2 ou tokens JWT, caso a API venha a ser exposta publicamente de forma mais ampla.
