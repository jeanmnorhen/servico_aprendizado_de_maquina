from ..domain.ports import IGeminiClient

class GenerateTextUseCase:
    def __init__(self, gemini_client: IGeminiClient):
        self.gemini_client = gemini_client

    def execute(self, prompt: str) -> dict:
        try:
            result = self.gemini_client.generate_text(prompt)
            return {"status": "SUCCESS", "result": result}
        except Exception as e:
            return {"status": "FAILURE", "error": str(e)}
