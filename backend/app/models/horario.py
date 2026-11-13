from datetime import datetime, time

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Time, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ConfiguracionHorarioDia(Base):
    __tablename__ = "configuracion_horario_dias"

    dia_semana: Mapped[int] = mapped_column(Integer, primary_key=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False, default=time(8, 0))
    hora_fin: Mapped[time] = mapped_column(Time, nullable=False, default=time(20, 0))
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
