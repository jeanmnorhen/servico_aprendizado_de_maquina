from typing import Optional, Any, List
import json
from pydantic import ValidationError

from ..domain.ports import ICeleryClient, IFileStorage, ILlavaClient, ISpriteCatalogService, IImagenClient
from ..domain.models import TaskTicket, TaskStatus, AnimationProcessRequest, GenerateProductDescriptionRequest
from ..schemas import SpriteAnalysisResult, AnimationChatRequest, AnimationChatResponse, AnimationSceneDescription

class TestTextWorkerUseCase:
    def __init__(self, celery_client: ICeleryClient):
        self.celery_client = celery_client

    def execute(self) -> dict:
        try:
            task = self.celery_client.send_task(
                'workers.text_worker.generate_product_description',
                kwargs={
                    "product_name_input": "carro de corrida vermelho",
                    "category_hint": None
                }, # Provide both arguments
                queue='text_queue'
            )
            # This is a blocking call, suitable only for a test endpoint
            result = task.get(timeout=300) # 5 minute timeout
            return {"status": "SUCCESS", "result": result}
        except Exception as e:
            return {"status": "FAILURE", "error": str(e)}

class ProcessAnimationScriptUseCase:
    def __init__(self, celery_client: ICeleryClient):
        self.celery_client = celery_client

    def execute(self, request_data: AnimationProcessRequest) -> TaskTicket:
        task = self.celery_client.send_task(
            'workers.text_worker.process_animation_script',
            args=[request_data.model_dump(exclude_none=True)],
            queue='text_queue'
        )
        return TaskTicket(task_id=task.id, status="PENDING")

class ProcessCatalogIntakeUseCase:
    def __init__(self, celery_client: ICeleryClient, file_storage: IFileStorage):
        self.celery_client = celery_client
        self.file_storage = file_storage

    def execute(self, file_content: Any, original_filename: str, project_id: Optional[str]) -> TaskTicket:
        file_path = self.file_storage.save_file(file_content, original_filename)
        task = self.celery_client.send_task(
            'workers.vision_worker.process_product_image',
            args=[str(file_path), project_id],
            queue='vision_queue'
        )
        return TaskTicket(task_id=task.id, status="PENDING")

class GenerateProductDescriptionUseCase:
    def __init__(self, celery_client: ICeleryClient):
        self.celery_client = celery_client

    def execute(self, request_data: GenerateProductDescriptionRequest) -> TaskTicket:
        task = self.celery_client.send_task(
            'workers.text_worker.generate_product_description',
            args=[request_data.product_name_input, request_data.category_hint],
            queue='text_queue'
        )
        return TaskTicket(task_id=task.id, status="PENDING")

class AnalyzeSpriteUseCase:
    def __init__(self, llava_client: ILlavaClient, sprite_catalog_service: ISpriteCatalogService):
        self.llava_client = llava_client
        self.sprite_catalog_service = sprite_catalog_service

    def execute(self, image_path: str) -> SpriteAnalysisResult:
        llava_prompt = """Analyze the provided sprite image in detail. Extract the following information and return it as a JSON object. Ensure the JSON strictly adheres to the specified schema.

        JSON Schema:
        {
          "name": "string", // A concise, human-readable name for the sprite (e.g., "Swordsman_Walk", "Forest_Background")
          "description": "string", // A detailed description of the sprite, including its appearance, pose, and any objects it holds.
          "keywords": "string[]", // A list of keywords or tags describing the sprite (e.g., "fantasy", "male", "sword", "walking", "animation", "character").
          "style": "string | null", // The artistic style of the sprite (e.g., "pixel art", "cartoon", "realistic").
          "character_type": "string | null", // The type of character or object (e.g., "humanoid", "monster", "prop", "animal", "background").
          "animation_frames": "number | null", // The number of animation frames detected in the sprite sheet. Infer if possible.
          "transparent_background": "boolean | null", // True if the sprite has a transparent background, False otherwise. Infer if possible.
          "suggested_skin_name": "string | null" // A suggested skin name for use in the animation system.
        }

        Example:
        {
          "name": "Swordsman_Walk",
          "description": "A male swordsman character in a fantasy style, wearing armor and holding a sword, in a walking pose. The sprite sheet contains multiple frames for a walking animation.",
          "keywords": ["fantasy", "male", "swordsman", "walking", "animation", "character"],
          "style": "pixel art",
          "character_type": "humanoid",
          "animation_frames": 8,
          "transparent_background": true,
          "suggested_skin_name": "Swordsman"
        }

        Provide ONLY the JSON object. Do not include any additional text or explanations.
        """

        response = self.llava_client.analyze_image(image_path=image_path, prompt=llava_prompt)

        if response["status"] == "SUCCESS":
            try:
                llava_response_content = response["response"]
                # Extract JSON from markdown code block if present
                if llava_response_content.strip().startswith("```json") and llava_response_content.strip().endswith("```"):
                    llava_response_content = llava_response_content.strip()[len("```json"): -len("```")].strip()

                analysis_dict = json.loads(llava_response_content)
                validated_result = SpriteAnalysisResult(**analysis_dict)
                self.sprite_catalog_service.add_sprite_metadata(validated_result, image_path) # Save to catalog
                return validated_result
            except json.JSONDecodeError as e:
                raise ValueError(f"LLaVA response was not valid JSON: {llava_response_content}")
            except ValidationError as e:
                raise ValueError(f"LLaVA response did not match the SpriteAnalysisResult schema: {llava_response_content}")
        else:
            raise RuntimeError(f"LLaVA API call failed: {response['error']}")

class ProcessAnimationChatUseCase:
    def __init__(self, celery_client: ICeleryClient, sprite_catalog_service: ISpriteCatalogService):
        self.celery_client = celery_client
        self.sprite_catalog_service = sprite_catalog_service

    def execute(self, request: AnimationChatRequest) -> AnimationChatResponse:
        # Retrieve active sprites from the catalog
        available_sprites = self.sprite_catalog_service.get_all_sprites_metadata()
        sprite_info = "\n".join([f"- {s.suggested_skin_name} ({s.name}): {s.description}" for s in available_sprites])

        # Construct the prompt for the LLM
        # This prompt needs to be carefully engineered to guide the LLM
        llm_prompt = f"""You are an AI animation assistant. Your goal is to help users create and modify animations based on their natural language requests. You have access to a catalog of sprites. When generating an animation, always use sprites from the provided catalog.

Available Sprites:
{sprite_info}

Conversation History:
{json.dumps(request.conversation_history, indent=2)}

Current Animation State:
{json.dumps(request.current_animation_state.model_dump() if request.current_animation_state else {}, indent=2)}

User: {request.user_message}

Based on the user's request, generate a natural language response and, if applicable, a new or modified AnimationSceneDescription JSON object. If the request is to create or modify an animation, provide the AnimationSceneDescription JSON. If the request is a question or requires clarification, provide a natural language response. If you generate an AnimationSceneDescription, ensure it is valid JSON and strictly adheres to the schema. Only output the JSON object if you are generating an animation. Otherwise, provide a natural language response.

AnimationSceneDescription JSON Schema:
{json.dumps(AnimationSceneDescription.model_json_schema(), indent=2)}

Your Response (natural language or JSON):
"""

        # Trigger Celery task for LLM processing
        task = self.celery_client.send_task(
            'workers.text_worker.process_animation_chat',
            args=[llm_prompt, request.current_animation_state.model_dump() if request.current_animation_state else None],
            queue='text_queue'
        )

        # For now, we'll return a placeholder response. The actual LLM response will be asynchronous.
        return AnimationChatResponse(
            llm_response="Processing your request...",
            new_animation_state=None,
            task_ticket=TaskTicket(task_id=task.id, status="PENDING")
        )

class GenerateImageUseCase:
    def __init__(self, imagen_client: IImagenClient, celery_client: ICeleryClient, sprite_catalog_service: ISpriteCatalogService):
        self.imagen_client = imagen_client
        self.celery_client = celery_client
        self.sprite_catalog_service = sprite_catalog_service

    def execute(self, prompt: str) -> dict:
        # Generate the image
        generated_image_path = self.imagen_client.generate_image(prompt)

        # Trigger LLaVA analysis for the generated image
        # This will add the generated image to the sprite catalog
        task = self.celery_client.send_task(
            'workers.vision_worker.analyze_generated_image',
            args=[generated_image_path],
            queue='vision_queue'
        )

        return {"image_path": generated_image_path, "analysis_task_id": task.id}

class GetTaskStatusUseCase:
    def __init__(self, celery_client: ICeleryClient):
        self.celery_client = celery_client

    def execute(self, task_id: str) -> TaskStatus:
        return self.celery_client.get_task_status(task_id)
