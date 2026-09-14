import asyncio

from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import UnidentifiedImageError

from modelo.yolo_model.modelo_base import analisar_conteudo, carregar_modelo

router = APIRouter()
model = carregar_modelo()  # Carrega o modelo YOLO ao iniciar o servidor
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024


async def ler_imagem(arquivo: UploadFile) -> bytes:
    content = await arquivo.read(MAX_IMAGE_SIZE_BYTES + 1)
    if len(content) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="A imagem excede o limite máximo de 10 MB.",
        )
    return content


@router.post("/predictAI")
async def predict(file: UploadFile = File(...)):
    """Recebe uma imagem em multipart."""
    try:
        content = await ler_imagem(file)
        return await asyncio.to_thread(analisar_conteudo, content, model=model)
    except HTTPException:
        raise
    except (ValueError, UnidentifiedImageError, OSError) as erro:
        raise HTTPException(
            status_code=400,
            detail="Imagem inválida ou corrompida.",
        ) from erro
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
            content = await ler_imagem(arquivo)
            resultado = await asyncio.to_thread(
                analisar_conteudo,
                content,
                model=model,
            )
            resultado.update(
                {
                    "indice": indice,
                    "nome_arquivo": arquivo.filename or f"imagem_{indice + 1}",
                }
            )
        except HTTPException as erro:
            resultado = {
                "indice": indice,
                "nome_arquivo": arquivo.filename or f"imagem_{indice + 1}",
                "status": "error",
                "erro": erro.detail,
                "status_code": erro.status_code,
            }
        except (ValueError, UnidentifiedImageError, OSError) as erro:
            resultado = {
                "indice": indice,
                "nome_arquivo": arquivo.filename or f"imagem_{indice + 1}",
                "status": "error",
                "erro": "Imagem inválida ou corrompida.",
                "status_code": 400,
            }
        except Exception:
            resultado = {
                "indice": indice,
                "nome_arquivo": arquivo.filename or f"imagem_{indice + 1}",
                "status": "error",
                "erro": "Erro interno ao processar imagem",
                "status_code": 500,
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