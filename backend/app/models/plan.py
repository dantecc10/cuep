from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

plan_materias = Table(
    "plan_materias",
    Base.metadata,
    Column("plan_id", ForeignKey("planes_estudio.id", ondelete="CASCADE"), primary_key=True),
    Column("materia_id", ForeignKey("materias.id", ondelete="CASCADE"), primary_key=True),
)


class PlanEstudio(Base):
    __tablename__ = "planes_estudio"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    nivel: Mapped[str] = mapped_column(String(20), nullable=False)
    area: Mapped[str | None] = mapped_column(String(50))
    descripcion: Mapped[str | None] = mapped_column(Text)
    activo: Mapped[bool] = mapped_column(default=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    materias = relationship("Materia", secondary=plan_materias, backref="planes")
