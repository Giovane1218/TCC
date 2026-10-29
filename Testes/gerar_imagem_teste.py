
from datetime import datetime
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image

limite = 5 * 1024 * 1024  # 5 MB
tamanho = 2500
pasta_destino = Path(__file__).resolve().parent / "arquivos_testes"
pasta_destino.mkdir(parents=True, exist_ok=True)
data_hora = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
caminho = pasta_destino / f"imagem_teste_{data_hora}.png"

while True:
    # Gera pixels aleatórios, dificultando a compressão
    pixels = np.random.randint(
        0, 256,
        (tamanho, tamanho, 3),
        dtype=np.uint8
    )
    imagem = Image.fromarray(pixels)
    imagem.save(caminho, format="PNG")

    tamanho_bytes = caminho.stat().st_size

    if tamanho_bytes > limite:
        break

    caminho.unlink()
    tamanho += 500

print(f"Imagem criada: {caminho}")
print(f"Tamanho: {tamanho_bytes / (1024 * 1024):.2f} MB")
