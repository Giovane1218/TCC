from core.exceptions import exceptions_type as erro
from core.exceptions.exceptions_msg import MENSSAGENS_ERRO

def ClassificarErro(e: Exception) -> tuple[int, str]:
    errorType = {
        erro.ImgSizeException: (413, MENSSAGENS_ERRO["IMG_SIZE_ERRO"]),
        erro.ConteudoInvalidoError: (422, MENSSAGENS_ERRO["INVALID_IMAGE_ERRO"]),
        erro.NoResultError: (400, MENSSAGENS_ERRO["NO_RESULT_ERRO"]),
        erro.PredictError: (400, MENSSAGENS_ERRO["PREDICT_ERROR"]),
        erro.ForbiddenError: (403, MENSSAGENS_ERRO["FORBIDDEN"]),
        erro.LoggedOutError: (401, MENSSAGENS_ERRO["LOGGED_OUT_ERROR"]),
        erro.LoginError: (401, MENSSAGENS_ERRO["LOGIN_ERROR"])
    }

    for tipo, msgError in errorType.items():   
        if isinstance(e, tipo):
            return msgError

    return (500, MENSSAGENS_ERRO["UNKNOW_ERROR"])
