Pontos de Melhoria


## Pontos de Melhoria

A criação de uma peça de teatro animada por inteligência artificial (IA) utilizando o modelo Gemma3 (via Ollama) como motor narrativo e o PixiJS para renderização 2D leve, exige uma arquitetura que converta eficientemente a descrição textual da IA em ativos visuais e posições precisas no Scene Graph.

Com a decisão de usar uma arquitetura self-hosted (Ollama/Celery/Redis) e focar na leveza, o principal desafio é evitar a geração de ativos complexos (como Text-to-Image de alta resolução) em tempo de execução, priorizando o reuso de ativos e a geração de geometria simples com o PixiJS Graphics.

**Arquitetura Assíncrona e Geração de Conteúdo**

O fluxo de trabalho adota um padrão assíncrono robusto, onde o Next.js atua como um Gateway para o cliente e o Celery gerencia as tarefas pesadas e de longa duração.

* Fluxo de Orquestração com Celery/Redis**

Nesta arquitetura, o Next.js (frontend) envia requisições narrativas ao Next.js API Route, que por sua vez:

1.  **Gatilho (Next.js):** Envia uma task para o Celery, recebendo um task_id imediato.
2.  **Processamento Assíncrono (Celery/Ollama):** O Celery Worker invoca o Gemma3 (via Ollama). O Gemma3 é forçado a gerar um Contrato de Dados JSON estruturado (conforme Tabela 1), contendo metadados de cena, instruções de movimento e, crucialmente, referências a ativos pré-existentes (URLs de spritesheets/partes) ou instruções de desenho de geometria.
3.  **Resultado (Redis):** O resultado final (JSON com URLs estáveis) é armazenado no backend de resultados do Redis.
4.  **Polling (Next.js/Cliente):** O cliente faz polling do task_id até que o resultado final seja retornado.

**O Contrato Gemma3/PixiJS (JSON Schema)**

O LLM (Gemma3) deve gerar um JSON que mapeie diretamente para comandos de renderização PixiJS. Isso garante a colocação correta de elementos, a ordem de profundidade e a referência aos ativos leves.

**Tabela 1. Estrutura JSON Schema para Saída do Gemma3 (Contrato de Renderização Otimizado)**

| Campo | Tipo | Descrição | Otimização/Uso PixiJS |
| :--- | :--- | :--- | :--- |
| `scene_id` | String | Identificador da cena. | Cache e reuso de ativos. |
| `background_type` | Enum (ImageURL, Graphics, TilingSprite) | Define como o fundo será desenhado. | Foco em Graphics ou TilingSprite para leveza. |
| `background_data` | Objeto | URL do ativo OU comandos de desenho (ex: `[{ rect: [x,y,w,h], fill: 'blue' }]`). | `GraphicsContext` para desenho vetorial. |
| `assets` | Array de Objetos | Lista de personagens e objetos (props). | Utiliza `Container` para agrupamento. |
| `assets[*].type` | Enum (CharacterModular, Spritesheet, PropGraphics) | Define o método de renderização. | Prioriza modulares ou spritesheets. |
| `assets[*].asset_id` | String | URL da textura ou Spritesheet JSON, ou tipo de forma básica. | Carregamento via `Assets.load()`. |
| `assets[*].parts` | Array de Objetos (apenas para Modular) | Componentes de Rigging (cabeça, braços, etc.). | Manipulação de `pivot`/`rotation` do `Container`. |
| `assets[*].position.x, y` | Number (0.0 a 1.0) | Posição normalizada (0 a 100%). | Conversão para coordenadas de tela PixiJS. |
| `assets[*].z_index` | Number | Profundidade relativa para ordenação. | `sortableChildren = true` no `Container` pai. |

**2. Desenho de Ativos Leves no PixiJS (O Lado Cliente)**

Para evitar modelos pesados (High-Res Textures), o PixiJS deve ser instruído a renderizar usando as formas mais leves: Spritesheets, Graphics (Vetorial) e composição modular.

**2.1. Desenho de Personagens (Atores)**

Em vez de gerar uma imagem completa (e inconsistente) para o personagem a cada frame, as duas abordagens mais leves são:

1.  **Rigging Modular com Container e Graphics (Desenho Vetorial Leve):** A IA (Gemma3) descreve os componentes (braço, tronco). Cada componente é um `Graphics` (para formas básicas) ou um `Sprite` (para texturas de partes).
    *   **Estrutura:** O personagem é um `Container` pai. Cada parte do corpo (e.g., `ArmContainer`, `HeadSprite`) é um filho.
    *   **Desenho de Forma Simples:** Partes do corpo (e.g., corpo retangular, cabeça circular) podem ser desenhadas diretamente como `Graphics`.
        ```javascript
        import { Graphics, Container } from 'pixi.js';
        const torso = new Graphics().rect(0, 0, 50, 100).fill('brown');
        const head = new Graphics().circle(25, 25, 25).fill('peach');
        const characterContainer = new Container();
        characterContainer.addChild(torso, head);
        // O PixiJS faz a 'rigging' da cabeça em relação ao torso via Container
        head.position.y = -50;
        ```
    *   **Animação:** A animação é feita manipulando as propriedades `rotation` e `pivot` dos `Containers` individuais (e.g., rotacionar um braço em torno de um ponto de pivot que simula o ombro).
    *   **Vantagem:** Extrema leveza, especialmente se a saída for `Graphics` (vetorial), pois a GPU renderiza a geometria diretamente, e não pixels de textura grandes.
2.  **Animação por Spritesheet (AnimatedSprite) (Performance Máxima):** O Gemma3 seleciona a spritesheet (ex: `walk_cycle.json`) mais apropriada. O PixiJS carrega o JSON e renderiza a animação frame-a-frame.
    *   **Vantagem:** Máxima otimização de renderização. O PixiJS pode renderizar dezenas de objetos em um único draw call se eles compartilharem a mesma `BaseTexture` (a spritesheet), um processo chamado batching. O `AnimatedSprite` foi projetado para isso.

**Desenho de Cenários e Objetos (Adereços)**

Para o cenário (fundo) e adereços estáticos, as estratégias de leveza são:

1.  **Fundos Repetitivos (TilingSprite):** Para céus, grama, ou padrões de parede, o `TilingSprite` é ideal. Ele repete uma pequena textura eficientemente para preencher grandes áreas.
2.  **Adereços Estáticos (Graphics ou Sprite Cacheado):**
    *   **Desenho Vetorial:** Para objetos simples (mesas, cadeiras, caixas), o `Graphics` pode gerar a forma mais rapidamente do que carregar uma textura.
    *   **Otimização de Cache:** Para fundos mais complexos ou adereços compostos, use `container.cacheAsTexture()` após o carregamento inicial. Isso renderiza a hierarquia complexa em uma única textura de GPU e a reutiliza em cada frame, reduzindo o draw call a um. É crucial usar isso apenas em objetos que não se movem com frequência.

**Gerenciamento de Profundidade e Camadas**

Para simular a profundidade teatral (Y-sorting), o PixiJS usa `Containers` e a propriedade `zIndex`.

**Hierarquia de Camadas:** A cena deve ser organizada em `Containers` lógicos para controlar a ordem de renderização.

| Container (Camada) | Propósito | Otimização PixiJS |
| :--- | :--- | :--- |
| `app.stage` (Raiz) | Gestão global. | Necessário. |
| `Layer: Backdrop` | Cenário e elementos fixos mais distantes. | `cacheAsTexture()` para fusão de todos os adereços estáticos em uma única chamada de desenho. |
| `Layer: Character Actors` | Contém todos os personagens (`Containers`/`Sprites`). | `sortableChildren = true` no `Container` pai. |
| `Layer: Foreground FX` | Elementos de UI, luzes, ou efeitos que devem estar no topo. | Prioridade de renderização alta (último a ser desenhado). |

**Ordenação Dinâmica (Z-Sorting):** Dentro da camada `Character Actors`, a ilusão de profundidade é alcançada ordenando dinamicamente os filhos com base em suas coordenadas Y (ou o `z_index` fornecido pela IA).


É vital chamar `sortChildren()` apenas quando a ordem de um personagem realmente muda, pois a classificação é uma operação com custo computacional.

*   **Expansão das Ações de Animação (Prioridade Média):**
    *   **Descrição:** O sistema atualmente suporta as ações `move`, `rotate`, `look_forward` e `walk_away`.
    *   **Solução Sugerida:** Expandir o `servico-ia-unificado` e o `AnimationEditor.tsx` para suportar mais ações, como `scale` (mudar de tamanho), `fade` (esmaecer), `speak` (exibir balão de fala), etc.

*   **Gerenciamento de Projetos (Prioridade Baixa):**
    *   **Descrição:** O editor funciona com um ID de projeto na URL, mas não há uma interface para o usuário criar, listar ou gerenciar seus projetos de forma mais intuitiva.
    *   **Solução Sugerida:** Criar uma nova página que liste os projetos do usuário e permita a criação de novos projetos, além de funcionalidades de edição e exclusão.
### Arquitetura

O fluxo de trabalho de IA será o seguinte:

1.  O **Frontend** (`Projeto_O_Cocriador`) envia uma requisição para o gateway de IA.
2.  O **Gateway de IA** (`unified_ai_api_gateway`) recebe a requisição, a valida e a enfileira como uma tarefa no **Celery**. Isso retorna um `task_id` imediatamente para o frontend.
3.  Um **Worker do Celery**, agora muito mais leve, pega a tarefa da fila.
4.  O Worker utiliza um novo **`OllamaClient`** para fazer uma chamada HTTP para a API do Ollama, que está rodando na máquina host.
5.  A comunicação entre o contêiner do worker e o host é feita através do endereço especial do Docker: `http://host.docker.internal:11434`.
6.  O **Ollama** processa a requisição usando o modelo `gemma3` (ou outro configurado) e retorna a resposta.
7.  O Worker do Celery recebe a resposta e a armazena no backend do Celery (Redis), finalizando a tarefa.
8.  O **Frontend** pode então usar o `task_id` para consultar o resultado.