from pathlib import Path
import numpy as np
from pydantic import BaseModel
import torch
import torch.nn as nn
from ultralytics import YOLO
import base64
import binascii
from typing import List
import cv2
import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from PIL import Image
import io




def carregar_modelo(path: str | None = None) -> YOLO:
    if path is None:
        path = str(Path(__file__).with_name("best.pt"))
    model = YOLO(path)
    return model


def decodificar_base64(valor: str) -> bytes:
    try:
        return base64.b64decode(valor, validate=True)
    except (binascii.Error, ValueError, TypeError) as erro:
        raise ValueError("Base64 inválido") from erro



class ImagemRequest(BaseModel):
    imagem_base64: str


class ImagemMultiplaItem(BaseModel):
    nome_arquivo: str = Field(min_length=1)
    imagem_base64: str


class ImagensRequest(BaseModel):
    imagens: List[ImagemMultiplaItem] = Field(min_length=1, max_length=20)


def analisar_conteudo(content: bytes, model: YOLO = None) -> dict:
    if model is None:
        model = carregar_modelo()
    """Processa a imagem usando o modelo YOLO treinado."""
    if not content:
        raise ValueError("Imagem vazia")

    if model is None:
        raise ValueError("O modelo YOLO não está carregado no servidor.")

    # 1. Converte bytes para imagem PIL / array NumPy RGB
    pil_image = Image.open(io.BytesIO(content)).convert("RGB")
    img_np = np.array(pil_image)

    # 2. Executa a predição com o YOLO
    results = model.predict(
        source=img_np,
        imgsz=1024,          # Resolução usada no treinamento
        conf=0.25,           # Threshold de confiança
        verbose=False
    )[0]

    # 3. Extrai as caixas delimitadoras e decide a frase de predição
    qtd_fraturas = len(results.boxes)
    predicao_str = "Fratura detectada" if qtd_fraturas > 0 else "Nenhuma fratura detectada"

    detections = []
    for box in results.boxes:
        xyxy = box.xyxy[0].tolist()
        detections.append({
            "confidence": round(float(box.conf[0]), 4),
            "bbox_pixel": {
                "xmin": round(xyxy[0], 2),
                "ymin": round(xyxy[1], 2),
                "xmax": round(xyxy[2], 2),
                "ymax": round(xyxy[3], 2)
            }
        })

    # 4. Desenha as caixas delimitadoras na imagem usando o helper plot() do YOLO
    annotated_frame_bgr = results.plot()  # Retorna em formato BGR do OpenCV

    #Adiiciona numeração às detecções
    for idx, box in enumerate(results.boxes, start=1):
        xyxy = box.xyxy[0].tolist()
        x1 = int(xyxy[0])
        y1 = int(xyxy[1])
        x2 = int(xyxy[2])
        y2 = int(xyxy[3])

        texto = str(idx)

        (largura, altura), _ = cv2.getTextSize(
            texto,
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            2
        )

        x_texto = x2 - largura - 10
        y_texto = y2 - 10

        cv2.putText(
            annotated_frame_bgr,
            texto,
            (x_texto, y_texto),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2,
            cv2.LINE_AA
        )

    # Codifica a imagem final anotada em PNG
    sucesso, buffer = cv2.imencode(".png", annotated_frame_bgr)
    if not sucesso:
        raise ValueError("Não foi possível codificar a imagem processada com as caixas.")

    return {
        "status": "success",
        "predicao": predicao_str,
        "total_fraturas": qtd_fraturas,
        "detecções": detections,
        "imagem_processada": base64.b64encode(buffer.tobytes()).decode("utf-8"),
        "detalhes": {"tamanho_bytes": len(content)},
    }