import random
import numpy as np
def analisar_imagem(imagem: np.ndarray) -> dict:
    imagem_analisada = imagem
    fratura = ["Fratura detectada", "Nenhuma fratura detectada", "Possível fratura, recomenda-se avaliação adicional"]
    resultado = random.choice(fratura)

    return {"resultado": resultado}