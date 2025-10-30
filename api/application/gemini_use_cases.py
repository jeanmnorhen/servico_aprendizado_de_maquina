from ..domain.ports import IGeminiClient, IChatRepository
from ..domain.models import ChatHistory
import uuid

class GenerateTextUseCase:
    def __init__(self, gemini_client: IGeminiClient, chat_repo: IChatRepository):
        self.gemini_client = gemini_client
        self.chat_repo = chat_repo

    def execute(self, prompt: str, session_id: str = None) -> dict:
        if not session_id:
            session_id = str(uuid.uuid4())
        
        try:
            # 1. Generate text using Gemini
            ai_response = self.gemini_client.generate_text(prompt)
            
            # 2. Persist the conversation
            history = ChatHistory(
                session_id=session_id,
                human_message=prompt,
                ai_message=ai_response
            )
            self.chat_repo.add(history)

            # 3. Return the result
            return {"status": "SUCCESS", "result": ai_response, "session_id": session_id}
        except Exception as e:
            return {"status": "FAILURE", "error": str(e)}
