import Src.Exeption.ExceptionsType as erro
from Src.Exeption.ExeptionsMenssages import MENSSAGENS_ERRO

def ClassificarErro(e: Exception) -> str:
    errorType = {
        erro.ImgSizeException: (413, MENSSAGENS_ERRO["IMG_SIZE_ERRO"]),
        erro.ConteudoInvalidoError: (422, MENSSAGENS_ERRO["INVALID_IMAGE_ERRO"]),
    }

    for tipo, msgError in errorType.items():
        if isinstance(e, tipo):
            return msgError
        
    return erro.UnknowError(500, MENSSAGENS_ERRO["UNKNOW_ERROR"])
    