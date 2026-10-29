from datetime import date

from pydantic import BaseModel, ConfigDict

from schemas.predict_result_schema import AnaliseCompletaResponse


class PacienteInfo(BaseModel):
    name: str
    sexo: str
    ladoAnalisado: str
    dataNcmto: date


class ReportRequest(BaseModel):
    pacienteInfo: PacienteInfo
    resultadosInfo: AnaliseCompletaResponse
