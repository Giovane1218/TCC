from pathlib import Path

import numpy as np
import torch
import torch.nn as nn


class BaselineCNN(nn.Module):

    def __init__(self):
        super().__init__()

        self.features = nn.Sequential(
            nn.Conv2d(in_channels=1, out_channels=32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(in_channels=32, out_channels=64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(in_channels=64, out_channels=128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )

        self.classifier = nn.Sequential(
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(),
            nn.Linear(128, 1),
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x


def preparar_tensor_entrada(imagem: np.ndarray) -> torch.Tensor:
    array = np.asarray(imagem, dtype=np.float32)

    if array.ndim == 2:
        array = array[:, :, None]

    if array.ndim == 3 and array.shape[-1] == 1:
        if array.shape[0] == 512 and array.shape[1] == 512:
            array = array[None, ...]
        elif array.shape[0] == 1 and array.shape[1] == 512 and array.shape[2] == 512:
            array = np.transpose(array, (0, 3, 1, 2))

    if array.ndim == 4 and array.shape[-1] == 1:
        array = np.transpose(array, (0, 3, 1, 2))

    tensor = torch.from_numpy(array)
    return tensor.float()


def carregar_modelo(path: str | None = None) -> BaselineCNN:
    device = torch.device("cpu")
    model = BaselineCNN()

    if path is None:
        path = str(Path(__file__).with_name("primeira_tentativa_pesos.pth"))

    checkpoint = torch.load(path, map_location=device)
    model.load_state_dict(checkpoint)
    model.to(device)
    model.eval()
    return model


def prever_imagem(imagem: np.ndarray, model: BaselineCNN | None = None) -> dict:
    if model is None:
        model = carregar_modelo()

    tensor = preparar_tensor_entrada(imagem)
    with torch.no_grad():
        logits = model(tensor)
        probabilidade = torch.sigmoid(logits).squeeze().item()

    resultado = "Fratura detectada" if probabilidade >= 0.5 else "Nenhuma fratura detectada"
    return {
        "resultado": resultado,
        "probabilidade": round(float(probabilidade), 4),
        "logit": round(float(logits.squeeze().item()), 4),
    }


def testar_modelo():
    model = carregar_modelo()
    tensor = preparar_tensor_entrada(np.zeros((512, 512, 1), dtype=np.float32))
    with torch.no_grad():
        output = model(tensor)
    return output

