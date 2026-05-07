from pydantic import BaseModel

class ImagemRequest(BaseModel):
    imagem_base64: str
    