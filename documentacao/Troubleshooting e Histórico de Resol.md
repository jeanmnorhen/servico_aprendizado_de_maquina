### Troubleshooting e Histórico de Resoluções

Este documento serve como referência para futuros diagnósticos de problemas relacionados à infraestrutura do serviço de IA.

1.  **Lentidão Extrema do Worker de IA (Original)**
    *   **Sintoma**: Um worker antigo, baseado em `llama-cpp-python` rodando em Docker, levava mais de uma hora para processar uma única tarefa.
    *   **Diagnóstico**: A execução de modelos de linguagem pesados dentro de um contêiner Docker sem aceleração de hardware adequada é extremamente ineficiente.
    *   **Solução**: Re-arquitetura completa do serviço de IA para utilizar o **Ollama**, rodando em um contêiner Docker, que provê uma performance drasticamente superior ao gerenciar o acesso ao hardware da máquina host.

2.  **Erro de Conexão entre Containers (Ex: `ECONNREFUSED` ou `NameResolutionError`)**
    *   **Sintoma**: Um container (ex: a API) não consegue se conectar a outro (ex: `ollama` ou `redis`).
    *   **Diagnóstico**: A tentativa de conexão usa `localhost`, que se refere ao próprio contêiner, ou o nome do serviço não é resolvido pela rede Docker.
    *   **Solução**: Utilizar o nome do serviço definido no `docker-compose.yml` como o hostname para a conexão (ex: `http://ollama:11434` ou `redis://redis:6379`).

3.  **Erro: `Bind for 0.0.0.0:6379 failed: port is already allocated`**
    *   **Sintoma**: O contêiner Redis não conseguia iniciar porque a porta `6379` já estava em uso.
    *   **Diagnóstico**: Um processo externo (ou um contêiner Docker antigo) estava utilizando a porta `6379`.
    *   **Solução**: Identificar e encerrar o processo que estava utilizando a porta no sistema operacional do host (no Windows: `netstat -ano` seguido de `taskkill /PID <PID> /F`). Um reinício do Docker Desktop também pode resolver.

4.  **Erro: `404 Client Error: Not Found for url: http://ollama:11434/api/chat`**
    *   **Sintoma**: O serviço Ollama respondia com `404` para o endpoint `/api/chat`.
    *   **Diagnóstico**: O modelo de IA (ex: `gemma`, `codellama`) não estava baixado ou carregado no contêiner Ollama.
    *   **Solução**: Garantir que os modelos necessários sejam puxados para o Ollama. Isso pode ser feito executando `docker-compose exec ollama ollama pull <nome-do-modelo>` ou garantindo que o serviço Ollama na máquina host tenha os modelos disponíveis.

5.  **Problemas de Conectividade Externa (GitHub, Docker Hub, etc.)**
    *   **Sintoma**: Falhas de `git pull`/`push` ou `docker-compose build` com erros como `Empty reply from server`, `Connection was reset`, ou `no such host`.
    *   **Diagnóstico**: Problema de rede na máquina host, geralmente relacionado a instabilidade da conexão ou resolução de DNS.
    *   **Solução**: 
        *   Verificar a conexão com a internet e o status do serviço externo (ex: [githubstatus.com](https://www.githubstatus.com/)).
        *   Executar `ping <host>` para verificar perda de pacotes.
        *   Limpar o cache de DNS local (no Windows: `ipconfig /flushdns`).
        *   Considerar a troca do servidor DNS da máquina host para um público (ex: `8.8.8.8`).
