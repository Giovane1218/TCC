import asyncio
from core import (
    ClassificarErro,
    analisar_conteudo, 
    ConteudoInvalidoError, 
    ImgSizeException)


MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024
MAX_IMAGES = 20

async def Execute(files, model):
    resultados = []
    try:
        if len(files) > MAX_IMAGES or len(files) <= 0:
            raise ConteudoInvalidoError
    except Exception as ex:
        status_code, menssagem = ClassificarErro(ex)

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
        status = "patial_succes"  

    return {
        "status": status,
        "total": len(resultados),
        "sucessos": sucessos,
        "erros": len(resultados) - sucessos,
        "resultados": resultados,}



async def ValidarImg(content):
    if len(content) > MAX_IMAGE_SIZE_BYTES:
        raise ImgSizeException
