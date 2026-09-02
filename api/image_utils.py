from pathlib import Path
import cv2
import numpy as np

imagems_dir = Path(__file__).resolve().parent.parent / "imagens"

def processar_imagem(conteudo: bytes, target_size: int):
    try:
        array = np.frombuffer(conteudo, np.uint8)
        imagem = cv2.imdecode(array, cv2.IMREAD_GRAYSCALE)

        if imagem is None:
            raise ValueError("Imagem inválida ou corrompida")

        # 1. Get original dimensions (height, width)
        old_size = imagem.shape[:2]

        # 2. Calculate the ratio to fit the longest side to the target size
        ratio = float(target_size) / max(old_size)
        new_size = tuple(int(x * ratio) for x in old_size)

        # 3. Resize safely (INTER_AREA is best for downsampling)
        img_resized = cv2.resize(
            imagem,
            (new_size[1], new_size[0]),
            interpolation=cv2.INTER_AREA,
        )

        # 4. Calculate how much black padding is needed to make it a square
        delta_w = target_size - new_size[1]
        delta_h = target_size - new_size[0]
        top, bottom = delta_h // 2, delta_h - (delta_h // 2)
        left, right = delta_w // 2, delta_w - (delta_w // 2)

        # 5. Add black borders (pixel value 0)
        final_xray = cv2.copyMakeBorder(
            img_resized,
            top,
            bottom,
            left,
            right,
            cv2.BORDER_CONSTANT,
            value=0,
        )
        final_xray = final_xray.astype(np.float32) / 255.0
        final_xray = np.expand_dims(final_xray, axis=(0, -1))  

        return final_xray
    except Exception as e:
        raise ValueError(f"Erro ao processar a imagem: {e}") from e