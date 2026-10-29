from pydantic import BaseModel


class ResultadoParcialResponse(BaseModel):
    sucesso: bool
    predict: str
    total_fraturas: int
    detections: list[dict]
    final_img: str


class ErroParcialResponse(BaseModel):
    sucesso: bool
    status_code: int
    erro: str
    file: str


class AnaliseCompletaResponse(BaseModel):
    status: str
    total: int
    sucessos: int
    erros: int
    resultados: list[ResultadoParcialResponse | ErroParcialResponse]
