from dataclasses import dataclass

@dataclass
class ImageCreate():
    url: str
@dataclass
class Image(ImageCreate):
    id: int