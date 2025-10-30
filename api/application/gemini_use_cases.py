from ..domain.ports import IChatRepository
from ..domain.models import ChatHistory
from ..infrastructure.model_factory import ModelFactory # Import the factory
import uuid

class GenerateTextUseCase:
    def __init__(self, model_factory: ModelFactory, chat_repo: IChatRepository):
        self.model_factory = model_factory
        self.chat_repo = chat_repo

    def execute(self, prompt: str, model: str, session_id: str = None) -> dict:
        if not session_id:
            session_id = str(uuid.uuid4())
        
        try:
            # 1. Get the correct text generator from the factory
            text_generator = self.model_factory.get_text_generator(model)

            # 2. Generate text using the selected generator
            ai_response = text_generator.generate_text(prompt, model)
            
            # 3. Persist the conversation
            history = ChatHistory(
                session_id=session_id,
                human_message=prompt,
                ai_message=ai_response
            )
            self.chat_repo.add(history)

            # 4. Return the result
            return {"status": "SUCCESS", "result": ai_response, "session_id": session_id}
        except Exception as e:
            return {"status": "FAILURE", "error": str(e)}
