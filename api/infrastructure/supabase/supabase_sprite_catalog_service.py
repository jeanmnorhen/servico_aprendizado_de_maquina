import os
from typing import List
from supabase import create_client, Client
from pathlib import Path # Import Path

from ...domain.ports import ISpriteCatalogService
from ...schemas import SpriteAnalysisResult

class SupabaseSpriteCatalogService(ISpriteCatalogService):
    def __init__(self, upload_dir: Path):
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.upload_dir = upload_dir

    def add_sprite_metadata(self, sprite_metadata: SpriteAnalysisResult, image_path: str) -> None:
        data_to_insert = sprite_metadata.model_dump()
        # Calculate the relative path from the upload directory
        relative_path = Path(image_path).relative_to(self.upload_dir)
        data_to_insert["image_path"] = f"/sprites/{relative_path}"
        data_to_insert["is_active"] = True # Set to active by default
        
        response = self.supabase.from_("sprites_metadata").insert(data_to_insert).execute()
        if response.data is None:
            raise Exception(f"Failed to insert sprite metadata: {response.error}")

    def get_all_sprites_metadata(self) -> List[SpriteAnalysisResult]:
        response = self.supabase.from_("sprites_metadata").select("*").eq("is_active", True).execute()
        if response.data is None:
            raise Exception(f"Failed to retrieve sprite metadata: {response.error}")
        
        # The image_path retrieved from Supabase is already the correct relative path
        return [SpriteAnalysisResult(**item) for item in response.data]

    def deactivate_sprite(self, image_path: str) -> None:
        response = self.supabase.from_("sprites_metadata").update({"is_active": False}).eq("image_path", image_path).execute()
        if response.data is None:
            raise Exception(f"Failed to deactivate sprite: {response.error}")