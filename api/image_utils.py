from pathlib import Path
import cv2
import numpy as np

imagems_dir = Path(__file__).resolve().parent.parent / "imagens"

def processar_imagem(conteudo: bytes) -> np.ndarray:

    try:
       np_array = np.frombuffer(conteudo, np.uint8)

       imagem = cv2.imdecode(np_array, cv2.IMREAD_GRAYSCALE)

       if imagem is None:
              raise ValueError("Imagem inválida ou corrompida")
       
       imagem  = cv2.resize(imagem, (224, 224))
       imagem = cv2.GaussianBlur(imagem, (5, 5), 0)
       clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
       imagem = clahe.apply(imagem)
       imagem = imagem.astype(np.float32) / 255.0

       imagem = np.expand_dims(imagem, axis=-1)

       imagem = np.expand_dims(imagem, axis=0)

       return imagem
        
    except Exception as e:
        raise ValueError(f"Erro ao processar a imagem: {e}")