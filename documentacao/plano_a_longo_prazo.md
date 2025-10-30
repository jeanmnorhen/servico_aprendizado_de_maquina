# Plano de Implementação (Longo Prazo)

Com a base do serviço de IA estabelecida, o foco a longo prazo é expandir suas capacidades, robustez e inteligência.

### Fase 1: Suporte a Múltiplas Modalidades

**Prioridade: Alta**

*   **Objetivo:** Expandir o serviço para além de texto, incluindo geração e análise de imagens.
*   **Ações:**
    1.  **Integrar Análise de Imagem:** Refatorar o `LlavaClient` para ser acessível através da `ModelFactory`, criando uma interface `IImageAnalyzer`.
    2.  **Criar Endpoint de Análise:** Desenvolver um novo endpoint (ex: `/api/ai/analyze-image`) que aceite uma imagem e um prompt.
    3.  **Integrar Geração de Imagem:** Adicionar suporte a um modelo de geração de imagem (ex: Stable Diffusion via Ollama) na `ModelFactory` e criar um endpoint correspondente.

---

### Fase 2: Gerenciamento e Inteligência de Conversa

**Prioridade: Média**

*   **Objetivo:** Tornar as conversas mais inteligentes e fáceis de gerenciar.
*   **Ações:**
    1.  **Endpoint de Histórico:** Criar um endpoint `GET /api/ai/chat-history/{session_id}` para recuperar o histórico completo de uma conversa.
    2.  **Injeção de Contexto:** Modificar o `GenerateTextUseCase` para, opcionalmente, recuperar o histórico de uma sessão e injetá-lo no prompt enviado ao LLM, permitindo conversas com memória.
    3.  **Gerenciamento de Uso:** Implementar uma lógica para rastrear o uso de tokens ou o número de chamadas por chave de API ou sessão.

---

### Fase 3: Produção e CI/CD

**Prioridade: Média**

*   **Objetivo:** Preparar o serviço para um ambiente de produção e automatizar o ciclo de desenvolvimento.
*   **Ações:**
    1.  **Testes:** Desenvolver uma suíte de testes unitários e de integração para garantir a confiabilidade do código.
    2.  **CI/CD (GitHub Actions):** Criar um workflow que automaticamente execute os testes, verifique a qualidade do código (linting) e construa as imagens Docker a cada push na branch principal.
    3.  **Estratégia de Deploy:** Definir uma estratégia para fazer o deploy dos serviços em um provedor de nuvem (ex: usando Kubernetes ou serviços de containers).