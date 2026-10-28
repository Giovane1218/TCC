import base64
import binascii
import re
from datetime import date
from io import BytesIO

from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
    PageBreak,
    KeepTogether,
)

from App.services.pdf_services import (
    _formatar_valor,
    _get,
    _idade,
    _imagem_base64,
    _texto,
)


async def ExecuteGerarPdf(db, usuarioAtual, pacienteInfo, resultados):
    arquivo = BytesIO()

    documento = SimpleDocTemplate(
        arquivo,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title="Relatório de Análise",
        author="Sistema de Análise Radiológica do Punho",
    )

    estilos = getSampleStyleSheet()

    estilos.add(
        ParagraphStyle(
            name="TituloRelatorio",
            parent=estilos["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=25,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#174A6E"),
            spaceAfter=8,
        )
    )

    estilos.add(
        ParagraphStyle(
            name="Subtitulo",
            parent=estilos["Heading2"],
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#174A6E"),
            spaceBefore=8,
            spaceAfter=7,
        )
    )

    estilos.add(
        ParagraphStyle(
            name="TextoRelatorio",
            parent=estilos["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            spaceAfter=4,
            wordWrap="CJK",
        )
    )

    estilos.add(
        ParagraphStyle(
            name="TituloImagem",
            parent=estilos["Heading3"],
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#174A6E"),
            spaceAfter=6,
        )
    )

    elementos = []

    # Aceita o schema Pydantic completo ou a lista diretamente.
    lista_resultados = _get(
        resultados,
        "resultados",
        default=resultados if isinstance(resultados, list) else [],
    )

    total = _get(resultados, "total", default=len(lista_resultados))
    sucessos = _get(
        resultados,
        "sucessos",
        default=sum(
            bool(_get(item, "sucesso", default=False)) for item in lista_resultados
        ),
    )
    erros = _get(
        resultados,
        "erros",
        default=total - sucessos,
    )

    # ---------------------------------------------------------
    # Cabeçalho
    # ---------------------------------------------------------
    elementos.append(Paragraph("Relatório de Análise", estilos["TituloRelatorio"]))
    elementos.append(Spacer(1, 8))

    elementos.append(
        Paragraph(
            f"Data de emissão: {date.today().strftime('%d/%m/%Y')}",
            estilos["TextoRelatorio"],
        )
    )
    elementos.append(Spacer(1, 12))

    # ---------------------------------------------------------
    # Dados do médico
    # Ajuste os nomes alternativos conforme seu modelo SQLAlchemy.
    # ---------------------------------------------------------
    elementos.append(Paragraph("Dados do médico", estilos["Subtitulo"]))

    nome_medico = _get(
        usuarioAtual,
        "username",
        default="Não informado",
    )
    funcao_medico = _get(
        usuarioAtual,
        "cargo",
        default="Não informado",
    )
    crm = _get(
        usuarioAtual,
        "registro_profissional",
        default="Não informado",
    )
    uf_crm = _get(
        usuarioAtual,
        "uf_registro",
        default="Não informado",
    )

    dados_medico = [
        [
            Paragraph("<b>Nome</b>", estilos["TextoRelatorio"]),
            Paragraph(_texto(nome_medico), estilos["TextoRelatorio"]),
            Paragraph("<b>Função</b>", estilos["TextoRelatorio"]),
            Paragraph(_texto(funcao_medico), estilos["TextoRelatorio"]),
        ],
        [
            Paragraph("<b>CRM</b>", estilos["TextoRelatorio"]),
            Paragraph(_texto(crm), estilos["TextoRelatorio"]),
            Paragraph("<b>UF do CRM</b>", estilos["TextoRelatorio"]),
            Paragraph(_texto(uf_crm), estilos["TextoRelatorio"]),
        ],
    ]

    tabela_medico = Table(
        dados_medico,
        colWidths=[2.5 * cm, 6 * cm, 3 * cm, 6.5 * cm],
    )

    tabela_medico.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EAF0F6")),
                ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#EAF0F6")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C7D2DC")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )

    elementos.append(tabela_medico)
    elementos.append(Spacer(1, 8))

    # ---------------------------------------------------------
    # Dados do paciente
    # ---------------------------------------------------------
    elementos.append(Paragraph("Dados do paciente", estilos["Subtitulo"]))

    nome_paciente = _get(pacienteInfo, "name", "nome")
    sexo = _get(pacienteInfo, "sexo")
    lado = _get(pacienteInfo, "ladoAnalisado", "lado_analisado")
    nascimento = _get(pacienteInfo, "dataNcmto", "data_nascimento")

    dados_paciente = [
        [
            Paragraph("<b>Nome</b>", estilos["TextoRelatorio"]),
            Paragraph(_texto(nome_paciente), estilos["TextoRelatorio"]),
            "",
            "",
        ],
        [
            Paragraph("<b>Data de nascimento</b>", estilos["TextoRelatorio"]),
            Paragraph(_texto(nascimento), estilos["TextoRelatorio"]),
            Paragraph("<b>Idade</b>", estilos["TextoRelatorio"]),
            Paragraph(
                f"{_idade(nascimento)} anos" if nascimento else "Não informada",
                estilos["TextoRelatorio"],
            ),
        ],
        [
            Paragraph("<b>Lado analisado</b>", estilos["TextoRelatorio"]),
            Paragraph(_texto(lado), estilos["TextoRelatorio"]),
            Paragraph("<b>Sexo</b>", estilos["TextoRelatorio"]),
            Paragraph(_texto(sexo), estilos["TextoRelatorio"]),
        ],
    ]

    tabela_paciente = Table(
        dados_paciente,
        colWidths=[3.5 * cm, 5.5 * cm, 3 * cm, 6 * cm],
    )

    tabela_paciente.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EAF0F6")),
                ("BACKGROUND", (2, 1), (2, -1), colors.HexColor("#EAF0F6")),
                ("SPAN", (1, 0), (3, 0)),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C7D2DC")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )

    elementos.append(tabela_paciente)
    elementos.append(Spacer(1, 8))

    # ---------------------------------------------------------
    # Panorama geral
    # ---------------------------------------------------------
    elementos.append(Paragraph("Panorama geral da análise", estilos["Subtitulo"]))

    resultados_validos = [
        item for item in lista_resultados if _get(item, "sucesso", default=False)
    ]

    total_fraturas = sum(
        int(_get(item, "total_fraturas", default=0) or 0) for item in resultados_validos
    )

    fratura_encontrada = total_fraturas > 0

    panorama = [
        [
            Paragraph(
                "<b>Imagens analisadas</b>",
                estilos["TextoRelatorio"],
            ),
            Paragraph(
                str(sucessos),
                estilos["TextoRelatorio"],
            ),
        ],
        [
            Paragraph(
                "<b>Indicação de fratura</b>",
                estilos["TextoRelatorio"],
            ),
            Paragraph(
                "Sim" if fratura_encontrada else "Não",
                estilos["TextoRelatorio"],
            ),
        ],
        [
            Paragraph(
                "<b>Total de fraturas</b>",
                estilos["TextoRelatorio"],
            ),
            Paragraph(
                str(total_fraturas),
                estilos["TextoRelatorio"],
            ),
        ],
    ]

    tabela_panorama = Table(
        panorama,
        colWidths=[6 * cm, 12 * cm],
    )

    tabela_panorama.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EAF0F6")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C7D2DC")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )

    elementos.append(tabela_panorama)
    elementos.append(Spacer(1, 8))

    # Começa os resultados individuais em uma página nova,
    # deixando espaço para acomodar dois itens por página.
    if resultados_validos:
        elementos.append(Paragraph("Resultados por imagem", estilos["Subtitulo"]))
        elementos.append(Spacer(1, 8))

    # ---------------------------------------------------------
    # Resultados individuais
    # ---------------------------------------------------------

    for indice, item in enumerate(resultados_validos, start=1):
        conteudo_imagem = _imagem_base64(_get(item, "final_img", default=""))

        imagem_pdf = None

        if conteudo_imagem:
            try:
                imagem_pdf = RLImage(
                    BytesIO(conteudo_imagem),
                    width=7.2 * cm,
                    height=5.2 * cm,
                    kind="proportional",
                )
            except ValueError, OSError:
                imagem_pdf = None

        total_fraturas = int(_get(item, "total_fraturas", default=0) or 0)

        detalhes = [
            Paragraph(
                f"Imagem {indice}",
                estilos["TituloImagem"],
            ),
            Paragraph(
                f"<b>Resultado:</b> {_texto(_get(item, 'predict'))}",
                estilos["TextoRelatorio"],
            ),
        ]

        detalhes.append(
            Paragraph(
                f"<b>Quantidade de fraturas:</b> {total_fraturas}",
                estilos["TextoRelatorio"],
            )
        )

        detections = _get(item, "detections", default=[]) or []

        if total_fraturas > 0:
            detalhes.append(
                Paragraph(
                    "<b>Nível de confiança da indicação:</b>",
                    estilos["TextoRelatorio"],
                )
            )

            for numero, deteccao in enumerate(detections, start=1):
                confianca = float(
                    _get(
                        deteccao,
                        "confidence",
                        "confianca",
                        "confiança",
                    )
                )

                # Converte para porcentagem se estiver entre 0 e 1.
                if 0 <= confianca <= 1:
                    confianca *= 100

                detalhes.append(
                    Paragraph(
                        f"Fratura {numero}: Confiança de {confianca:.1f}%",
                        estilos["TextoRelatorio"],
                    )
                )
        else:
            detalhes.append(
                Paragraph(
                    "Nenhuma indicação de fratura foi encontrada",
                    estilos["TextoRelatorio"],
                )
            )

        if imagem_pdf:
            celulas = [[imagem_pdf, detalhes]]
        else:
            celulas = [
                [
                    Paragraph(
                        "Imagem indisponível",
                        estilos["TextoRelatorio"],
                    ),
                    detalhes,
                ]
            ]

        tabela_imagem = Table(
            celulas,
            colWidths=[7.6 * cm, 10.4 * cm],
        )

        tabela_imagem.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#F2F5F8")),
                    ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#C7D2DC")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D8E0E7")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (0, 0), (0, 0), "CENTER"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )

        elementos.append(
            KeepTogether(
                [
                    tabela_imagem,
                    Spacer(1, 12),
                ]
            )
        )

    # ---------------------------------------------------------
    # Assinatura do médico
    # ---------------------------------------------------------
    elementos.append(Spacer(1, 25))

    assinatura = Table(
        [
            [""],
            [
                Paragraph(
                    f"<b>{_texto(nome_medico)}</b>",
                    estilos["TextoRelatorio"],
                )
            ],
            [
                Paragraph(
                    f"CRM: {_texto(crm)} - {_texto(uf_crm)}",
                    estilos["TextoRelatorio"],
                )
            ],
            [
                Paragraph(
                    "Assinatura do médico",
                    estilos["TextoRelatorio"],
                )
            ],
        ],
        colWidths=[9 * cm],
    )

    assinatura.setStyle(
        TableStyle(
            [
                ("LINEABOVE", (0, 1), (0, 1), 0.8, colors.black),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("MINROWHEIGHT", (0, 0), (0, 0), 1.5 * cm),
            ]
        )
    )

    elementos.append(
        KeepTogether(
            [
                assinatura,
            ]
        )
    )

    documento.build(elementos)

    arquivo.seek(0)
    return arquivo
