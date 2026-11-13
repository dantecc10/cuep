from datetime import date

from pydantic import BaseModel, ConfigDict
from typing import Optional, List


class CorridaCreate(BaseModel):
    sede_id: int
    grupo_ids: List[int]
    parametros: Optional[dict] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None


class PublicarCorridaRequest(BaseModel):
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None


class CorridaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sede_id: Optional[int] = None
    config_hash: str
    aprobada: bool = False
    publicada: bool = False
    estado: str
    solicitado_por: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    parametros_resumen: Optional[dict] = None
    resultado_json: Optional[dict] = None
    metricas_optimizacion: Optional[dict] = None
    intentos: int = 0
    progreso: int = 0
    etapa: Optional[str] = None
