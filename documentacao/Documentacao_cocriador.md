### Projeto `O_Cocriador`

`O_Cocriador` é uma aplicação inovadora para criação de animações 2D assistida por IA. Ele permite que o usuário gere animações complexas a partir de descrições textuais e, em seguida, refine-as com ajustes finos baseados em texto ou manipulação direta de keyframes.

**Arquitetura:**

*   **Frontend (Next.js)**: Interface principal da aplicação, onde o usuário insere roteiros de animação, gerencia personagens e visualiza a animação gerada em um canvas PixiJS. Utiliza **Server Actions** para se comunicar com o serviço de IA. O componente `AnimationEditor.tsx` é responsável por interpretar a `AnimationSceneDescription` e renderizar a animação no canvas PixiJS, utilizando sprites para personagens e aplicando transformações baseadas em keyframes.

*   **Arquitetura do Motor de Animação (PixiJS)**: Para garantir a leveza e a performance, a arquitetura de renderização se baseia em instruir a IA a gerar um JSON estruturado que o PixiJS possa interpretar de forma eficiente. As principais estratégias são:
    *   **Desenho Vetorial com `Graphics`**: Em vez de imagens pesadas, a IA descreve os personagens e objetos como formas geométricas (retângulos, círculos) que o PixiJS desenha diretamente na GPU.
    *   **Rigging Modular com `Container`**: Personagens são compostos por partes (cabeça, tronco, membros) organizadas em `Containers`. A animação é feita manipulando a posição e rotação desses `Containers`, criando um sistema de "esqueleto" vetorial.
    *   **Otimização com `Spritesheets` e `TilingSprite`**: Para animações repetitivas (como ciclos de caminhada) e fundos, são utilizados `Spritesheets` e `TilingSprites` para otimizar o número de `draw calls`.
    *   **Gerenciamento de Profundidade**: A propriedade `zIndex` e a ordenação de `Containers` (`sortableChildren`) são usadas para criar a ilusão de profundidade no palco 2D.
    *   Para um detalhamento técnico completo, consulte o **[Blueprint Arquitetural no Plano de Desenvolvimento](Plano_de_Desenvolvimento_Projeto_O_Cocriador.md#22-blueprint-arquitetural-para-animação-teatral-dinâmica-2d-com-gemma3-nextjs-e-pixijs-otimizado-para-leveza)**.
*   **Banco de Dados (Supabase)**: Persiste os dados dos projetos, personagens e keyframes criados manualmente ou gerados pela IA.
*   **Serviço de IA (`servico-ia-unificado`)**: Atua como um orquestrador e gateway. Ele recebe requisições do frontend, as enfileira como tarefas assíncronas usando Celery, e as executa chamando um serviço de modelo de linguagem externo.
*   **Motor de IA (Ollama)**: O processamento de linguagem natural é realizado por um serviço **Ollama rodando em um contêiner Docker**. O `servico-ia-unificado` se comunica com a API do Ollama para gerar o conteúdo de texto e as instruções de animação.

**Como executar (localmente):**

1.  **Inicie os Serviços do Projeto (Docker):**
    *   Navegue até o diretório `D:\Oficina\servico-ia-unificado`.
    *   Execute `docker-compose up --build -d` para iniciar os serviços de backend (Redis, API Gateway, Celery Worker e Ollama).
    *   **Aguarde alguns minutos** para que o contêiner Ollama baixe o modelo `gemma3` e inicie completamente.
    *   Navegue de volta para o diretório raiz `D:\Oficina`.
    *   Execute `docker-compose up --build -d` para iniciar o frontend.

2.  **Acesse a Aplicação:**
    *   O frontend estará acessível em [http://localhost:3000](http://localhost:3000).

---

### Serviço `servico-ia-unificado`

Este serviço não executa mais o modelo de IA diretamente. Ele atua como um gateway que valida as requisições, gerencia tarefas assíncronas com Celery e se comunica com a API do Ollama rodando em um contêiner Docker.

**Componentes:**

*   **API Gateway (FastAPI)**: Expõe os endpoints para o frontend.
*   **Cliente Ollama**: Um cliente HTTP interno responsável por fazer as chamadas para a API do Ollama (`http://ollama:11434`).
*   **Celery**: Usado para enfileirar as chamadas à API do Ollama, evitando que o frontend fique bloqueado esperando a resposta.

**Variáveis de Ambiente (`.env` do `servico-ia-unificado`):**

*   `REDIS_URL`: String de conexão para o Redis, usado como broker do Celery.
*   `INTERNAL_SERVICE_SECRET`: Chave secreta para garantir que apenas os serviços autorizados possam acessar a API.
*   `OLLAMA_API_URL`: A URL completa para a API do Ollama. **Para desenvolvimento local, esta URL está hardcoded no `ollama_client.py` como `http://ollama:11434` para garantir a comunicação entre contêineres.**

---
