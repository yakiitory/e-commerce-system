from __future__ import annotations
import os
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image

if TYPE_CHECKING:
    from fastapi import UploadFile


class MediaService:
    """
    Handles business logic for saving and processing media files, like images.
    """

    def __init__(self, media_root: str | Path = "media"):
        """
        Initializes the MediaService and creates necessary subdirectories.

        Args:
            media_root (str | Path): The root directory for storing media files.
                                     Defaults to 'db-images' relative to the project root.
        """
        # Resolving the path to ensure it's absolute and exists.
        # This assumes the service is run from the project root context.
        self.media_dir = Path(media_root).resolve() # e.g., /path/to/project/db-images
        self.products_dir = self.media_dir / "products"
        self.reviews_dir = self.media_dir / "reviews"
        self.products_dir.mkdir(parents=True, exist_ok=True)
        self.reviews_dir.mkdir(parents=True, exist_ok=True)

    def save_image(self, image: UploadFile, image_id: int) -> tuple[bool, str | None]:
        """
        Saves an uploaded image, compresses it, and converts it to JPEG.

        The image is saved with a filename corresponding to the given integer ID.
        For example, an image_id of 123 will be saved as '123.jpg'.

        Args:
            image (UploadFile): The uploaded image file from a web framework like FastAPI.
            image_id (int): The integer to use as the base filename.

        Returns:
            A tuple containing a boolean for success and the relative path to the saved
            image, or `None` on failure.
        """
        if not image.content_type.startswith("image/"):
            return (False, None)

        try:
            # Define the output path
            file_name = f"{image_id}.jpg"
            output_path = self.products_dir / file_name

            # Open the uploaded image using Pillow
            pil_image = Image.open(image.file)

            # Convert to RGB if it has an alpha channel (like PNGs)
            if pil_image.mode in ("RGBA", "P"):
                pil_image = pil_image.convert("RGB")

            # Save the image as a compressed JPEG
            pil_image.save(output_path, "jpeg", quality=85, optimize=True)

            # Return a relative path suitable for web URLs
            relative_path = Path(self.media_dir.name) / self.products_dir.name / file_name
            # Use forward slashes for web paths, regardless of OS
            return (True, str(relative_path).replace(os.path.sep, '/'))
        except Exception as e:
            print(f"[MediaService ERROR] Failed to save image {image_id}: {e}")
            return (False, None)

    def delete_image(self, relative_path: str) -> bool:
        """
        Deletes an image file from the filesystem.

        Args:
            relative_path (str): The relative path to the image file, as stored in the DB.
                                 e.g., 'db-images/products/123.jpg'

        Returns:
            bool: True if the file was deleted or did not exist, False on error.
        """
        try:
            # Construct the full absolute path to the file
            # Assumes the media_root is the parent of the first directory in relative_path
            file_path = self.media_dir.parent / Path(relative_path)
            if file_path.exists():
                file_path.unlink()
                return True
            return True # File didn't exist, which is a success state for deletion
        except Exception as e:
            print(f"[MediaService ERROR] Failed to delete image at {relative_path}: {e}")
            return False
