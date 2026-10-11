
from PIL import Image
import numpy as np
import os

limite = 5 * 1024 * 1024  # 5 MB
tamanho = 2500

while True:
    # Gera pixels aleatórios, dificultando a compressão
    pixels = np.random.randint(
        0, 256,
        (tamanho, tamanho, 3),
        dtype=np.uint8
    )

    imagem = Image.fromarray(pixels)
    caminho = "imagem_teste.png"
    imagem.save(caminho, format="PNG")

    tamanho_bytes = os.path.getsize(caminho)

    if tamanho_bytes > limite:
        break

    tamanho += 500

print(f"Imagem criada: {caminho}")
print(f"Tamanho: {tamanho_bytes / (1024 * 1024):.2f} MB")
