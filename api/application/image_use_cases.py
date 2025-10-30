from ..domain.ports import IImageGenerator

class GenerateImageUseCase:
    def __init__(self, image_generator: IImageGenerator):
        self.image_generator = image_generator

    def execute(self, prompt: str) -> dict:
        try:
            image_path = self.image_generator.generate_image(prompt)
            return {"status": "SUCCESS", "image_path": image_path}
        except Exception as e:
            return {"status": "FAILURE", "error": str(e)}
