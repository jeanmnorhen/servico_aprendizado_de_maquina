### Troubleshooting e Histórico de Resoluções

Durante o desenvolvimento, a comunicação entre o `ocriador_frontend` e o `servico-ia-unificado` apresentou uma série de desafios. A seguir, um resumo dos problemas e suas soluções, servindo como referência para futuros diagnósticos.

1.  **Lentidão Extrema do Worker de IA (Original)**
    *   **Sintoma**: O worker original, baseado em `llama-cpp-python` rodando em Docker, levava mais de uma hora para processar uma única tarefa.
    *   **Diagnóstico**: A execução de modelos de linguagem pesados dentro de um contêiner Docker sem aceleração de hardware adequada é extremamente ineficiente.
    *   **Solução**: Re-arquitetura completa do serviço de IA para utilizar o **Ollama**, rodando em um contêiner Docker, que provê uma performance drasticamente superior.

2.  **Erro: `ECONNREFUSED ::1:8009`**
    *   **Sintoma**: O frontend não conseguia se conectar à API de IA.
    *   **Diagnóstico**: O `fetch` no Next.js (dentro do contêiner Docker) estava tentando se conectar ao `localhost`, que se refere ao próprio contêiner, não ao contêiner da API.
    *   **Solução**: A variável de ambiente `UNIFIED_AI_API_URL` foi alterada para `http://unified_ai_api:8000`, utilizando o nome do serviço Docker e a porta interna.

3.  **Erro: `TypeError: '<' not supported...` ao chamar `send_task`**
    *   **Sintoma**: O serviço de IA falhava ao enfileirar uma tarefa no Celery.
    *   **Diagnóstico**: A função `send_task` do Celery estava sendo chamada com o nome da fila (`queue`) como um argumento posicional, que era interpretado incorretamente como o argumento `countdown`.
    *   **Solução**: A chamada da função foi modificada para usar argumentos nomeados (`kwargs`), passando a fila corretamente.

4.  **Problema: `OLLAMA_API_URL` não sendo reconhecida (backend)**
    *   **Sintoma**: O `unified_ai_text_worker` tentava se conectar a uma URL `OLLAMA_API_URL` antiga (e.g., `http://172.22.80.1:11434`) mesmo após as configurações no `docker-compose.yml` e `.env`.
    *   **Diagnóstico**: Uma variável de ambiente `OLLAMA_API_URL` persistente no sistema operacional do host estava sobrescrevendo as configurações do Docker Compose, mesmo com `env_file`.
    *   **Solução**: A `OLLAMA_API_URL` foi hardcoded no `servico-ia-unificado/api/infrastructure/ollama_client.py` para `http://ollama:11434`, e o `Dockerfile.worker` foi ajustado para refletir o comando correto de `ollama serve`. **Para evitar futuros conflitos, é recomendado verificar e remover `OLLAMA_API_URL` das variáveis de ambiente globais do sistema Windows.**

5.  **Erro: `Bind for 0.0.0.0:6379 failed: port is already allocated` (backend)**
    *   **Sintoma**: O contêiner Redis não conseguia iniciar porque a porta `6379` já estava em uso.
    *   **Diagnóstico**: Um processo externo (ou um contêiner Docker antigo) estava utilizando a porta `6379`.
    *   **Solução**: Identificar e encerrar o processo que estava utilizando a porta `6379` no sistema operacional do host (`netstat -ano` seguido de `taskkill /PID <PID> /F`). Um reinício do Docker Desktop também pode resolver.

6.  **Erro: `NameResolutionError: Failed to resolve 'ollama'` (backend)**
    *   **Sintoma**: O `unified_ai_text_worker` não conseguia resolver o nome do host `ollama`.
    *   **Diagnóstico**: O serviço `ollama` não estava em execução ou não estava acessível na rede Docker.
    *   **Solução**: Garantir que o `docker-compose up` fosse executado no diretório correto do `servico-ia-unificado` para iniciar o serviço `ollama`. A correção do `entrypoint` no `docker-compose.yml` também foi essencial.

7.  **Erro: `404 Client Error: Not Found for url: http://ollama:11434/api/chat` (backend)**
    *   **Sintoma**: O serviço Ollama respondia com `404` para o endpoint `/api/chat`.
    *   **Diagnóstico**: O modelo Gemma3 não estava carregado no contêiner Ollama.
    *   **Solução**: Ajustar o `entrypoint` do serviço Ollama no `docker-compose.yml` para garantir que o comando `ollama serve` seja executado corretamente e o modelo `gemma3` seja baixado automaticamente na inicialização (`ollama serve & ollama pull gemma3 && wait`).

8.  **Erro: `getaddrinfo ENOTFOUND unified_ai_api` (frontend)**
    *   **Sintoma**: O frontend tentava se conectar ao `unified_ai_api` e falhava na resolução de nome.
    *   **Diagnóstico**: O frontend estava rodando diretamente no host e tentava resolver o nome interno do serviço Docker.
    *   **Solução**: Hardcode da URL da API do `servico-ia-unificado` para `http://localhost:8000` em `Projeto_O_Cocriador/src/app/editor/[projectId]/actions.ts`, pois a porta 8000 é exposta pelo contêiner `unified_ai_api` ao host.

9.  **Erro: `column projetos.user_id does not exist` (frontend/Supabase)**
    *   **Sintoma**: As funções do frontend para listar ou criar projetos tentavam acessar a coluna `user_id` da tabela `projetos`, que havia sido removida para desativar o login.
    *   **Diagnóstico**: O código do frontend ainda referenciava a coluna `user_id` em consultas e inserções.
    *   **Solução**: Remover todas as referências a `user_id` nas funções `createProject`, `listProjects` e `getProjectDataAction` no frontend, e ajustar as políticas de Row Level Security (RLS) no Supabase para permitir acesso público, já que não há `user_id` para filtrar.

10. **Erro: `invalid input syntax for type uuid: "hero"` e `duplicate key value violates unique constraint "personagens_pkey"` (Supabase)**
    *   **Sintoma**: Falha ao inserir personagens no Supabase devido a IDs de UUID inválidos e violação de chave primária.
    *   **Diagnóstico**: A IA gerava `id`s de string ("hero") enquanto a coluna na tabela `personagens` esperava um UUID. Além disso, a `personagens_pkey` estava apenas no `id`, levando a conflitos em múltiplos projetos.
    *   **Solução**: Alterar o tipo da coluna `personagens.id` para `TEXT`. Em seguida, redefinir a chave primária da tabela `personagens` para ser uma chave primária composta de `(id, projeto_id)`. Isso permite que o ID de personagem seja único por projeto. O uso de `upsert` no código foi mantido para a inserção/atualização flexível.

11. **Erro: `Uncaught TypeError: app.stage.toFront is not a function` (frontend/PixiJS)**
    *   **Sintoma**: Erro durante a manipulação de sprites no PixiJS.
    *   **Diagnóstico**: O método `toFront()` não está mais disponível em versões recentes do PixiJS.
    *   **Solução**: Substituir `app.stage.toFront(sprite)` pela lógica de `app.stage.removeChild(sprite); app.stage.addChild(sprite);` para reordenar o sprite para a frente.

12. **Problema: Animação não visível (frontend)**
    *   **Sintoma**: O sprite era exibido, mas não se movia.
    *   **Diagnóstico**: O componente `AnimationEditor.tsx` não interpretava corretamente todas as ações geradas pela IA (`look_forward`, `walk_away`) e a inicialização `char.pontos_pivo` estava incorreta.
    *   **Solução**:
        *   Adicionar lógica no `switch (step.action)` para as ações `look_forward` e `walk_away` (e expandir `move`).
        *   Corrigir o acesso à posição inicial do personagem para usar `char.initial_position` (da AI) ou `char.pontos_pivo` (do DB).
        *   Confirmação de que `tl.play()` era chamado e `step.params` era válido.
