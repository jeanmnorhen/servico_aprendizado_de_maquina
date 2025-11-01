import os
import json
from typing import Optional

from pydantic import ValidationError
from config.celery_config import celery_app
from api.infrastructure.ollama_client import OllamaClient
from api.schemas import ProductData, GenerateProductDescriptionRequest, GeneratedProductDescription




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
