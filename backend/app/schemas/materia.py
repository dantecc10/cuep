from pydantic import BaseModel, ConfigDict


class MateriaCreate(BaseModel):
    nombre: str
    nivel: str
    area: str


class MateriaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    nivel: str
    area: str
