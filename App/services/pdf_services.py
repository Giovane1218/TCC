import base64
import binascii
from datetime import date
import re
from xml.sax.saxutils import escape


def _get(obj, *nomes, default=None):
    """Obtém um atributo de um objeto ou uma chave de dicionário."""
    for nome in nomes:
        if isinstance(obj, dict):
            valor = obj.get(nome)
        else:
            valor = getattr(obj, nome, None)

        if valor is not None:
            return valor

    return default


def _texto(valor):
    """Converte valores em texto seguro para o ReportLab."""
    if valor is None or valor == "":
        return "Não informado"

    if isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")

    return escape(str(valor))


def _idade(data_nascimento):
    """Calcula a idade considerando se o aniversário já ocorreu."""
    hoje = date.today()

    if isinstance(data_nascimento, str):
        data_nascimento = date.fromisoformat(data_nascimento)

    idade = hoje.year - data_nascimento.year

    if (hoje.month, hoje.day) < (
        data_nascimento.month,
        data_nascimento.day,
    ):
        idade -= 1

    return idade


def _imagem_base64(conteudo):
    """Converte Base64 em bytes para o ReportLab."""
    if not conteudo:
        return None

    # Aceita Base64 puro ou uma data URL.
    if conteudo.startswith("data:") and "," in conteudo:
        conteudo = conteudo.split(",", 1)[1]

    conteudo = re.sub(r"\s+", "", conteudo)

    try:
        return base64.b64decode(conteudo, validate=True)
    except binascii.Error, ValueError:
        return None


def _formatar_valor(valor):
    """Formata valores das detecções, inclusive dicionários."""
    if isinstance(valor, dict):
        return ", ".join(
            f"{chave}: {_formatar_valor(item)}" for chave, item in valor.items()
        )

    if isinstance(valor, list):
        return "; ".join(_formatar_valor(item) for item in valor)

    return str(valor)
