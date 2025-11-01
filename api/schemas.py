from pydantic import BaseModel, Field
from typing import List, Optional, Union, Any

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
    result: Optional[Union[ProductData, GeneratedProductDescription]] = None
    error: Optional[str] = None
