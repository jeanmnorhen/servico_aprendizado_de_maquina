import os
import json
from typing import Optional

from pydantic import ValidationError
from config.celery_config import celery_app
from api.infrastructure.ollama_client import OllamaClient
from api.schemas import AnimationProcessRequest, AnimationSceneDescription
from api.infrastructure.supabase.supabase_sprite_catalog_service import SupabaseSpriteCatalogService

@celery_app.task(name='workers.text_worker.process_animation_script')
def process_animation_script(request_data_dict: dict):
    """Processes an animation script using the Ollama client."""
    request_data = AnimationProcessRequest(**request_data_dict)
    ollama_client = OllamaClient()
    sprite_catalog_service = SupabaseSpriteCatalogService() # Instantiate the service

    # Keywords for RAG search in the PixiJS documentation
    keywords = ["Sprite", "Container", "gsap", "to", "rotation", "scale", "alpha", "move", "position", "pixi.js", "Graphics", "rect", "circle", "fill", "zIndex", "sortableChildren", "cacheAsTexture", "TilingSprite", "pivot", "drawRect", "drawCircle"]

    # Dynamically retrieve available sprites from the catalog
    available_sprites_metadata = sprite_catalog_service.get_all_sprites_metadata()
    available_sprites_str = ""
    if available_sprites_metadata:
        available_sprites_str = "\n\n**Sprites Catalogados Disponíveis:**\n"
        for sprite in available_sprites_metadata:
            available_sprites_str += f"- Nome: {sprite.suggested_skin_name or sprite.name}, Descrição: {sprite.description}\n"

    system_prompt = f"""Você é um assistente de IA especialista em criar cenas 2D para o PixiJS usando spritesheets.

**Sua tarefa é converter um roteiro em um objeto JSON que descreve a cena, os personagens e as animações, selecionando os ativos de uma lista pré-definida.**

**Ativos Disponíveis:**
- **Skins de Personagem:** `Archer`, `Enchantress`, `Knight`, `Musketeer`, `Swordsman`, `Wizard`.
- **Animações Disponíveis para cada skin:** `Attack_1`, `Attack_2`, `Attack_3`, `Dead`, `Hurt`, `Idle`, `Run`, `Walk`, `Jump`.

**Fundos Disponíveis:**
Você pode escolher um dos seguintes temas de fundo. O caminho completo será construído automaticamente.
- `Floresta Cartum` (usa `/sprites/background/Cartoon_Forest_BG_01/layer_01.png`)
- `Cidade` (usa `/sprites/background/City1/layer_01.png`)
- `Exterior Geral` (usa `/sprites/background/exterior.png`)
- `Interior Geral` (usa `/sprites/background/Interior.png`)

{available_sprites_str}

**Processo de Raciocínio:**
1.  **Identifique os Personagens:** Leia o roteiro e identifique os personagens (ex: "uma mulher loira", "um cavaleiro").
2.  **Selecione a Skin:** Para cada personagem, escolha a `skin` mais apropriada da lista de skins disponíveis OU dos sprites catalogados. Para "uma mulher loira", `Enchantress` é uma boa escolha.
3.  **Defina as Animações:** Determine a sequência de ações. Para fazer um personagem andar, você DEVE gerar DUAS etapas em `animation_steps`:
    *   Uma etapa para definir a animação: `{{ "action": "play_animation", "params": {{ "animation": "Walk" }} }}`.
    *   Uma etapa separada para o movimento: `{{ "action": "move", "duration": 5, "params": {{ "x": 0.8 }} }}`.
4.  **Selecione o Fundo:** Escolha o tema de fundo mais adequado ao roteiro e construa o `background_url`.
5.  **Monte o JSON Final:** Construa o objeto `AnimationSceneDescription` com os ativos e passos de animação definidos.

**Estrutura do JSON (Contrato de Renderização):**
Sua saída DEVE ser um JSON com a seguinte estrutura:

```json
{{
  "scene_id": "string",
  "background_url": "string | null",
  "assets": [
    {{
      "asset_id": "string",
      "skin": "string", // Skin escolhida da lista
      "position": {{ "x": "number", "y": "number" }}, // Posição normalizada 0.0-1.0
      "z_index": "number"
    }}
  ],
  "animation_steps": [
    {{
      "target_id": "string", // asset_id
      "action": "'move' | 'play_animation'",
      "duration": "number", // em segundos
      "params": {{ 
          "animation": "string", // para play_animation (ex: 'Walk')
          "x": "number", // para move
          "y": "number" // para move
      }}
    }}
  ]
}}
```

**REVISE SUA SAÍDA** para garantir que ela corresponda **EXATAMENTE** à estrutura e aos nomes de campo definidos.
**Sua resposta DEVE ser um único objeto JSON, sem nenhum texto ou explicação adicional.**
"""

    user_prompt = f"""Transforme o seguinte esboço de cena e personagens em um roteiro de animação e instruções PixiJS, seguindo o contrato JSON definido:

Esboço da Cena: "{request_data.script}"

{f"Estado atual da animação para refinamento: {json.dumps(request_data.current_animation_state.model_dump_json() if request_data.current_animation_state else None)}" if request_data.current_animation_state else ""}

Gere a `AnimationSceneDescription` completa em um único bloco JSON."""

    full_prompt = f"{system_prompt}\n\n{user_prompt}"

    try:
        result = ollama_client.generate(prompt=full_prompt, keywords=keywords)
        
        if result["status"] == "SUCCESS":
            try:
                animation_description_dict = json.loads(result["response"])
                validated_description = AnimationSceneDescription(**animation_description_dict)
                return validated_description.model_dump()
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from Ollama: {e}")
                raise ValueError(f"Ollama response was not valid JSON: {result['response']}")
            except ValidationError as e:
                print(f"Pydantic validation error: {e}")
                raise ValueError(f"Ollama response did not match the AnimationSceneDescription schema: {result['response']}")
        else:
            raise RuntimeError(f"Ollama API call failed: {result['error']}")

    except Exception as e:
        print(f"Error during Ollama inference for animation script: {e}")
        raise e

@celery_app.task(name='workers.text_worker.generate_product_description')
def generate_product_description(product_name_input: str, category_hint: Optional[str] = None):
    """Generates a product description using the Ollama client."""
    ollama_client = OllamaClient()

    system_prompt = """Você é um assistente de IA. Sua tarefa é gerar um nome de produto, uma descrição e uma categoria, com base nas informações fornecidas. Sua resposta DEVE ser um objeto JSON válido com as chaves 'nome', 'descrição' e 'categoria'."""

    user_prompt = f"""Gere um nome, descrição e categoria para um produto com base nas seguintes informações:
Nome/Palavras-chave: {product_name_input}
{f'Sugestão de Categoria: {category_hint}' if category_hint else ''}

Responda APENAS com o objeto JSON, sem nenhum texto ou explicação adicional."""

    full_prompt = f"{system_prompt}\n\n{user_prompt}"

    try:
        result = ollama_client.generate(prompt=full_prompt)
        
        if result["status"] == "SUCCESS":
            try:
                product_description = json.loads(result["response"])
                return product_description
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from Ollama: {e}")
                raise ValueError(f"Ollama response was not valid JSON: {result['response']}")
        else:
            raise RuntimeError(f"Ollama API call failed: {result['error']}")

    except Exception as e:
        print(f"Error during Ollama inference for product description generation: {e}")
        raise e

@celery_app.task(name='workers.text_worker.simple_test_task')
def simple_test_task():
    """A simple test task that uses the Ollama client."""
    ollama_client = OllamaClient()
    print("Sending simple test task to Ollama...")
    result = ollama_client.generate(prompt="Why is the sky blue?")
    print(f"Ollama response: {result}")
    return result

@celery_app.task(name='workers.text_worker.generate_product_description')
def generate_product_description(product_name_input: str, category_hint: Optional[str] = None):
    """Generates a product description using the Ollama client."""
    ollama_client = OllamaClient()

    system_prompt = """Você é um assistente de IA. Sua tarefa é gerar um nome de produto, uma descrição e uma categoria, com base nas informações fornecidas. Sua resposta DEVE ser um objeto JSON válido com as chaves 'nome', 'descrição' e 'categoria'."""

    user_prompt = f"""Gere um nome, descrição e categoria para um produto com base nas seguintes informações:
Nome/Palavras-chave: {product_name_input}
{f'Sugestão de Categoria: {category_hint}' if category_hint else ''}

Responda APENAS com o objeto JSON, sem nenhum texto ou explicação adicional."""

    full_prompt = f"{system_prompt}\n\n{user_prompt}"

    try:
        result = ollama_client.generate(prompt=full_prompt)
        
        if result["status"] == "SUCCESS":
            try:
                product_description = json.loads(result["response"])
                return product_description
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from Ollama: {e}")
                raise ValueError(f"Ollama response was not valid JSON: {result['response']}")
        else:
            raise RuntimeError(f"Ollama API call failed: {result['error']}")

    except Exception as e:
        print(f"Error during Ollama inference for product description generation: {e}")
        raise e

@celery_app.task(name='workers.text_worker.simple_test_task')
def simple_test_task():
    """A simple test task that uses the Ollama client."""
    ollama_client = OllamaClient()
    print("Sending simple test task to Ollama...")
    result = ollama_client.generate(prompt="Why is the sky blue?")
    print(f"Ollama response: {result}")
    return result
