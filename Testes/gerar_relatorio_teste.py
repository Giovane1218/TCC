import asyncio
import base64
from datetime import date, datetime
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

from App.usecases.ReportUseCase.report_useCase import ExecuteGerarPdf


def criar_imagem_ilustrativa() -> str:
    imagem = Image.new("RGB", (640, 420), "#343b42")
    desenho = ImageDraw.Draw(imagem)
    desenho.rectangle((230, 45, 410, 375), fill="#b9c3ca")
    desenho.ellipse((250, 28, 390, 95), fill="#cbd2d7")
    desenho.line((275, 95, 285, 340), fill="#eef1f3", width=12)
    desenho.line((320, 95, 325, 360), fill="#eef1f3", width=12)
    desenho.line((365, 95, 355, 340), fill="#eef1f3", width=12)

    buffer = BytesIO()
    imagem.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


async def main() -> None:
    medico = {
        "username": "Médico de Teste",
        "cargo": "Radiologista (dado fictício)",
        "registro_profissional": "000000",
        "uf_registro": "SP",
    }
    paciente = {
        "name": "Paciente Fictício - Teste de PDF",
        "sexo": "Não informado",
        "ladoAnalisado": "Esquerdo (teste)",
        "dataNcmto": date(1990, 1, 1),
    }
    resultados = {
        "status": "concluido",
        "total": 1,
        "sucessos": 1,
        "erros": 0,
        "resultados": [
            {
                "sucesso": True,
                "predict": "Resultado fictício para teste do relatório",
                "total_fraturas": 1,
                "detections": [
                    {
                        "classe": "detecção simulada",
                        "confidence": 0.97,
                        "bbox": [120, 80, 260, 210],
                    }
                ],
                "final_img": criar_imagem_ilustrativa(),
            }
        ],
    }

    pdf = await ExecuteGerarPdf(None, medico, paciente, resultados)
    conteudo = pdf.getvalue()
    if not conteudo.startswith(b"%PDF"):
        raise RuntimeError("O gerador não retornou um PDF válido.")

    pasta_destino = Path(__file__).resolve().parent / "arquivos_testes"
    pasta_destino.mkdir(parents=True, exist_ok=True)
    data_hora = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    destino = pasta_destino / f"relatorio_teste_{data_hora}.pdf"
    destino.write_bytes(conteudo)
    print(f"Relatório fictício salvo em: {destino}")


if __name__ == "__main__":
    asyncio.run(main())
