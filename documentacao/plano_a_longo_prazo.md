##  Plano de Implementação das Funcionalidades (Longo Prazo)

### **Fase 1: Gerenciamento de Poses (O Estúdio de Coreografia)**

**Prioridade: Alta**

*   **Passo 1: Backend (Supabase)**
    *   **Ação:** Criar uma nova tabela `poses` (`id`, `user_id`, `name`, `pose_data`).

*   **Passo 2: Camada de Dados (Server Actions)**
    *   **Ação:** Criar server actions para gerenciar as poses: `createPose`, `getPoses`, etc.

*   **Passo 3: UI (Novos Componentes)**
    *   **Ação:** Desenvolver `PoseEditor.tsx` com **Pixi-IK**.
    *   **Ação:** Desenvolver `PoseLibrary.tsx` para exibir as poses salvas.

*   **Passo 4: Integração**
    *   **Ação:** Modificar `EditorClient.tsx` e `AnimationEditor.tsx` para aplicar as poses salvas.

---

### **Fase 2: Gerenciamento de Figurinos (O Departamento de Figurinos)**

**Prioridade: Média**

*   **Passo 1: Backend (Supabase)**
    *   **Ação:** Criar tabelas `costume_items` e `character_outfits`.

*   **Passo 2: UI e Integração**
    *   **Ação:** Criar `WardrobePanel.tsx`.
    *   **Ação:** Refatorar `AnimationEditor.tsx` para renderizar figurinos em camadas.

---

### **Fase 3: Controle de Câmera (A Direção)**

**Prioridade: Média**

*   **Passo 1: Refatoração do Motor de Renderização**
    *   **Ação:** Implementar um objeto `camera` e um contêiner "mundo" em `AnimationEditor.tsx`.

*   **Passo 2: UI e Animação**
    *   **Ação:** Integrar o controle da câmera com GSAP e adicionar uma faixa de câmera na `Timeline`.

*   **Passo 3: Integração com IA**
    *   **Ação:** Expandir o prompt da IA para incluir instruções de câmera.
