import io
import base64

from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image as PDFImage,
    PageBreak,
)
from reportlab.lib.utils import ImageReader


def gerar_pdf(resultados, arquivos_por_indice):
    buffer_pdf = io.BytesIO()

    documento = SimpleDocTemplate(
        buffer_pdf,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    estilos = getSampleStyleSheet()

    estilo_titulo = estilos["Title"]
    estilo_titulo.alignment = TA_CENTER

    estilo_subtitulo = estilos["Heading2"]

    elementos = []

    elementos.append(
        Paragraph(
            "Relatório de Análise de Radiografias do Punho",
            estilo_titulo
        )
    )

    elementos.append(Spacer(1, 15))

    data_hora = datetime.now().strftime("%d/%m/%Y às %H:%M")

    elementos.append(
        Paragraph(
            f"<b>Data e hora da análise:</b> {data_hora}",
            estilos["Normal"]
        )
    )

    elementos.append(Spacer(1, 20))

    for indice, resultado in enumerate(resultados, start=1):

        nome = resultado.get(
            "nome_arquivo",
            f"Imagem {indice}"
        )

        elementos.append(
            Paragraph(
                f"Imagem {indice}: {nome}",
                estilo_subtitulo
            )
        )

        elementos.append(Spacer(1, 8))

        if resultado.get("status") != "success":
            erro = resultado.get(
                "erro",
                "Erro desconhecido"
            )

            elementos.append(
                Paragraph(
                    f"<b>Erro:</b> {erro}",
                    estilos["Normal"]
                )
            )

            elementos.append(PageBreak())
            continue

        predicao = resultado.get(
            "predicao",
            "Resultado indisponível"
        )

        total_fraturas = resultado.get(
            "total_fraturas",
            0
        )

        elementos.append(
            Paragraph(
                f"<b>Resultado:</b> {predicao}",
                estilos["Normal"]
            )
        )

        elementos.append(
            Paragraph(
                f"<b>Fraturas detectadas:</b> {total_fraturas}",
                estilos["Normal"]
            )
        )

        elementos.append(Spacer(1, 10))

        detections = resultado.get("detecções", [])

        for numero, detection in enumerate(
            detections,
            start=1
        ):
            confianca = detection.get("confidence")

            if confianca is not None:
                elementos.append(
                    Paragraph(
                        f"<b>Fratura {numero}:</b> "
                        f"Confiança da detecção: "
                        f"{confianca:.2%}",
                        estilos["Normal"]
                    )
                )

        elementos.append(Spacer(1, 15))

        indice_original = resultado.get("indice", indice - 1)
        arquivo = arquivos_por_indice.get(indice_original)

        if arquivo is not None:
            imagem_original = io.BytesIO(arquivo.getvalue())
            imagem_original.seek(0)
            elementos.append(
                Paragraph(
                    "<b>Imagem original</b>",
                    estilos["Normal"]
                )
            )

            elementos.append(Spacer(1, 5))

            elementos.append(
                PDFImage(
                    imagem_original,
                    width=240,
                    height=240,
                    kind="proportional"
                )
            )

            elementos.append(Spacer(1, 15))

        imagem_processada = resultado.get(
            "imagem_processada"
        )

        if imagem_processada:
            imagem_processada = io.BytesIO(base64.b64decode(imagem_processada))
            imagem_processada.seek(0)

            elementos.append(
                Paragraph(
                    "<b>Imagem processada</b>",
                    estilos["Normal"]
                )
            )

            elementos.append(Spacer(1, 5))

            elementos.append(
                PDFImage(
                    imagem_processada,
                    width=240,
                    height=240,
                    kind="proportional"
                )
            )

        elementos.append(PageBreak())

    elementos.append(
        Paragraph(
            "<b>Observação:</b> Este sistema foi desenvolvido "
            "para fins acadêmicos e de pesquisa. Os resultados "
            "apresentados não substituem a avaliação ou o "
            "diagnóstico realizado por um profissional de saúde.",
            estilos["Normal"]
        )
    )

    documento.build(elementos)

    buffer_pdf.seek(0)

    return buffer_pdf