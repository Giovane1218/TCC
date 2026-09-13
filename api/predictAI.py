from fastapi import APIRouter, File, HTTPException, UploadFile

from modelo.yolo_model.modelo_base import analisar_conteudo, carregar_modelo

router = APIRouter()
model = carregar_modelo()  # Carrega o modelo YOLO ao iniciar o servidor


@router.post("/predictAI")
async def predict(file: UploadFile = File(...)):
    """Recebe uma imagem em multipart."""
    try:
        content = await file.read()
        return analisar_conteudo(content, model=model)
    except ValueError as erro:
        raise HTTPException(status_code=400, detail=str(erro)) from erro
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao processar imagem",
        )


@router.post("/predictAI/multiple")
async def predict_ai_multiple(files: list[UploadFile] = File(...)):
    """Recebe várias imagens em multipart e devolve o resultado de cada uma."""
    resultados = []

    if not 1 <= len(files) <= 20:
        raise HTTPException(status_code=400, detail="Envie entre 1 e 20 imagens.")

    for indice, arquivo in enumerate(files):
        try:
            content = await arquivo.read()
            resultado = analisar_conteudo(content, model=model)
            resultado.update(
                {
                    "indice": indice,
                    "nome_arquivo": arquivo.filename or f"imagem_{indice + 1}",
                }
            )
        except ValueError as erro:
            resultado = {
                "indice": indice,
                "nome_arquivo": arquivo.filename or f"imagem_{indice + 1}",
                "status": "error",
                "erro": str(erro),
            }
        except Exception as erro:
            resultado = {
                "indice": indice,
                "nome_arquivo": arquivo.filename or f"imagem_{indice + 1}",
                "status": "error",
                "erro": f"Erro interno: {str(erro)}",
            }

        resultados.append(resultado)

    sucessos = sum(item["status"] == "success" for item in resultados)
    return {
        "status": "success" if sucessos == len(resultados) else "partial_success",
        "total": len(resultados),
        "sucessos": sucessos,
        "erros": len(resultados) - sucessos,
        "resultados": resultados,
    }