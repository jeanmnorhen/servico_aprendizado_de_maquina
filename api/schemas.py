from pydantic import BaseModel, Field
from typing import List, Optional, Union, Any
from enum import Enum

# --- Enums ---
class AssetTypeEnum(str, Enum):
    ANIMATED_SPRITE = "AnimatedSprite"

# --- Schemas para Projeto O_Cocriador (Animação) ---

class Asset(BaseModel):
    asset_id: str = Field(..., description="ID único para o ativo.")
    skin: str = Field(..., description="A skin do personagem a ser usada (ex: 'Swordsman', 'Enchantress').")
    position: dict = Field(..., description="Posição inicial normalizada do ativo no palco {'x', 'y'}.")
    z_index: int = Field(..., description="Ordem de profundidade para simular o eixo Z.")

class AnimationStep(BaseModel):
    target_id: str = Field(..., description="O asset_id a ser animado.")
    action: str = Field(..., description="Ação a ser executada (ex: 'move', 'play_animation').")
    duration: float = Field(..., description="Duração da animação em segundos.")
    params: dict = Field(..., description="Parâmetros da animação (ex: {'x': 0.8} para move, {'animation': 'Walk'} para play_animation).")

class AnimationSceneDescription(BaseModel):
    scene_id: str = Field(..., description="Identificador único para a cena.")
    background_url: Optional[str] = Field(None, description="URL para uma imagem de fundo estática.")
    assets: List[Asset] = Field(..., description="Lista de todos os personagens e objetos de cena.")
    animation_steps: List[AnimationStep] = Field(..., description="Sequência de animações a serem executadas.")

class AnimationProcessRequest(BaseModel):
    script: str = Field(..., description="O roteiro de animação a ser processado.")
    project_id: str = Field(..., description="ID do projeto de animação.")
    current_animation_state: Optional[AnimationSceneDescription] = Field(None, description="Estado atual da animação para refinamento iterativo.")

class AnimationChatRequest(BaseModel):
    user_message: str = Field(..., description="A mensagem do usuário em linguagem natural.")
    conversation_history: List[dict] = Field([], description="Histórico da conversa para manter o contexto.")
    current_animation_state: Optional[AnimationSceneDescription] = Field(None, description="Estado atual da animação para modificações iterativas.")

class AnimationChatResponse(BaseModel):
    llm_response: str = Field(..., description="A resposta do LLM em linguagem natural.")
    new_animation_state: Optional[AnimationSceneDescription] = Field(None, description="O novo estado da animação gerado ou modificado.")
    task_ticket: Optional[TaskTicket] = Field(None, description="Ticket da tarefa assíncrona, se aplicável.")

class GenerateImageRequest(BaseModel):
    prompt: str = Field(..., description="O prompt de texto para gerar a imagem.")
    aspect_ratio: Optional[str] = Field("1:1", description="A proporção da imagem gerada (ex: '1:1', '16:9').")
    person_generation: Optional[str] = Field("allow_adult", description="Opções para geração de pessoas (ex: 'dont_allow', 'allow_adult', 'allow_all').")


# --- Schemas para Sprite Analysis ---
class SpriteAnalysisResult(BaseModel):
    name: str = Field(..., description="A concise, human-readable name for the sprite.")
    description: str = Field(..., description="A detailed description of the sprite, including its appearance, pose, and any objects it holds.")
    keywords: List[str] = Field(..., description="A list of keywords or tags describing the sprite (e.g., 'fantasy', 'male', 'sword', 'walking').")
    style: Optional[str] = Field(None, description="The artistic style of the sprite (e.g., 'pixel art', 'cartoon', 'realistic').")
    character_type: Optional[str] = Field(None, description="The type of character or object (e.g., 'humanoid', 'monster', 'prop', 'animal', 'background').")
    animation_frames: Optional[int] = Field(None, description="The number of animation frames detected in the sprite sheet.")
    transparent_background: Optional[bool] = Field(None, description="True if the sprite has a transparent background, False otherwise.")
    suggested_skin_name: Optional[str] = Field(None, description="A suggested skin name for use in the animation system.")
    is_active: bool = Field(True, description="Indicates if the sprite is active or soft-deleted.")


# --- Schemas para Projeto PrecoReal (Catálogo de Produtos) ---
class ProductData(BaseModel):
    product_name: str = Field(description="Nome de e-commerce conciso e otimizado para o produto.")
    category_standard: str = Field(description="Categoria de alto nível do produto (ex: 'Eletrônicos', 'Alimentos', 'Vestuário').")
    description_long: str = Field(description="Descrição rica em detalhes, materiais e benefícios, com no mínimo 50 palavras.")
    features_list: List[str] = Field(description="Uma lista de três a cinco características ou 'selling points' principais do produto.")

class GenerateProductDescriptionRequest(BaseModel):
    product_name_input: str = Field(..., description="Nome ou palavras-chave do produto fornecidas pelo lojista.")
    category_hint: Optional[str] = Field(None, description="Sugestão de categoria para a IA.")

class GeneratedProductDescription(BaseModel):
    suggested_name: str = Field(..., description="Nome de produto sugerido pela IA.")
    suggested_description: str = Field(..., description="Descrição de produto sugerida pela IA.")
    suggested_category: str = Field(..., description="Categoria de produto sugerida pela IA.")

# --- Schemas para Respostas de Tarefas ---
class TaskTicket(BaseModel):
    task_id: str
    status: str = "PENDING"

class TaskStatus(BaseModel):
    task_id: str
    status: str
    result: Optional[Union[ProductData, GeneratedProductDescription, AnimationSceneDescription, SpriteAnalysisResult]] = None
    error: Optional[str] = None