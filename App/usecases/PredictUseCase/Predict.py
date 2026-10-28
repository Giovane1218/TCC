import asyncio
import io
import warnings
from PIL import Image
from core import (
    ClassificarErro,
    analisar_conteudo,
    ConteudoInvalidoError,
    ImgSizeException,
    MAX_IMAGE_SIZE_BYTES,
)

async def Execute(files, model):
    resultados = []
    for file in files:
        try:
            content = await file.read(MAX_IMAGE_SIZE_BYTES + 1)
            await ValidarImg(content)
            resultado = await asyncio.to_thread(
                analisar_conteudo,
                content,
                model=model,
            )
            resultados.append(resultado)

        except Exception as ex:
            status_code, menssagem = ClassificarErro(ex)
            resultados.append({
                "sucesso": False,
                "status_code": status_code,
                "erro": menssagem,
                "file": file.filename
                })

    sucessos = sum(item["sucesso"] == True for item in resultados)

    if sucessos == len(resultados):
        status = "total_success"
    elif sucessos == 0:
        status = "fail"
    else: 
        status = "partial_success"

    return {
        "status": status,
        "total": len(resultados),
        "sucessos": sucessos,
        "erros": len(resultados) - sucessos,
        "resultados": resultados,}


async def ValidarImg(content: bytes) -> None:
    if len(content) > MAX_IMAGE_SIZE_BYTES:
        raise ImgSizeException
    if not content:
        raise ConteudoInvalidoError

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as image:
                image.verify()

            with Image.open(io.BytesIO(content)) as image:
                image.load()
    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        OSError,
        SyntaxError,
        ValueError,
    ) as exc:
        raise ConteudoInvalidoError from exc
