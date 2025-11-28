from __future__ import annotations
import os
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image

if TYPE_CHECKING:
    from werkzeug.datastructures import FileStorage


class MediaService:
    """
    Handles business logic for saving and processing media files, like images.
    """

    def __init__(self, media_root: str | Path = "media"):
        """
        Initializes the MediaService.

        Args:
            media_root (str | Path): The root directory for storing media files.
                                     Defaults to 'media' relative to the project root.
        """
        # Resolving the path to ensure it's absolute and exists.
        # This assumes the service is run from the project root context.
        self.media_dir = Path(media_root).resolve()
        self.media_dir.mkdir(parents=True, exist_ok=True)

    def _save_image(self, image: FileStorage, image_id: int, subdirectory: str) -> tuple[bool, str | None]:
        """
        Saves an uploaded image to a specific subdirectory, compresses it, and converts it to JPEG.

        The image is saved with a filename corresponding to the given integer ID.
        For example, an image_id of 123 will be saved as '123.jpg'.

        Args:
            image (FileStorage): The uploaded image file from a web framework like Flask.
            image_id (int): The integer to use as the base filename.
            subdirectory (str): The subdirectory within the media root to save the image in.

        Returns:
            A tuple containing a boolean for success and the relative path to the saved
            image, or `None` on failure.
        """
        if not image.content_type or not image.content_type.startswith("image/"):
            return (False, "Invalid file type. Only images are allowed.")

        try:
            # Create the specific subdirectory if it doesn't exist
            target_dir = self.media_dir / subdirectory
            target_dir.mkdir(exist_ok=True)

            # Define the output path
            file_name = f"{image_id}.jpg"
            output_path = target_dir / file_name

            # Open the uploaded image using Pillow
            pil_image = Image.open(image.stream)

            # Convert to RGB if it has an alpha channel (like PNGs)
            if pil_image.mode in ("RGBA", "P"):
                pil_image = pil_image.convert("RGB")

            # Save the image as a compressed JPEG
            pil_image.save(output_path, "jpeg", quality=85, optimize=True)

            # Return the relative path including the media root and subdirectory
            relative_path = str(Path(self.media_dir.name) / subdirectory / file_name)
            return (True, relative_path)
        except Exception as e:
            print(f"[MediaService ERROR] Failed to save image for ID {image_id}: {e}")
            return (False, "Failed to process and save the image.")

    def save_product_image(self, image: FileStorage, image_id: int) -> tuple[bool, str | None]:
        """
        Saves an image for a product.

        Args:
            image (FileStorage): The uploaded image file.
            image_id (int): The ID of the image record.

        Returns:
            A tuple containing success status and the relative path to the image.
        """
        return self._save_image(image, image_id, "products")

    def save_review_image(self, image: FileStorage, image_id: int) -> tuple[bool, str | None]:
        """
        Saves an image for a review.

        Args:
            image (FileStorage): The uploaded image file.
            image_id (int): The ID of the image record.

        Returns:
            A tuple containing success status and the relative path to the image.
        """
        return self._save_image(image, image_id, "reviews")

    def delete_image(self, relative_path: str) -> bool:
        """
        Deletes an image file from the media directory.

        Args:
            relative_path (str): The relative path of the image to delete,
                                 as stored in the database (e.g., 'src/static/db-images/products/123.jpg').

        Returns:
            bool: True if the file was deleted successfully or did not exist, False on error.
        """
        if not relative_path:
            return False

        try:
            # Construct the full, absolute path to the image file
            full_path = Path(os.getcwd()) / relative_path
            
            # Check if the file exists and delete it
            if full_path.is_file():
                full_path.unlink()
            return True
        except Exception as e:
            print(f"[MediaService ERROR] Failed to delete image at {relative_path}: {e}")
            return False
