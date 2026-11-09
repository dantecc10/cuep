from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido_paterno: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido_materno: Mapped[str | None] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="tutor")
    es_tutor: Mapped[bool] = mapped_column(Boolean, default=False)
    telefono: Mapped[str | None] = mapped_column(String(30))
    biografia_md: Mapped[str | None] = mapped_column(String)
    foto_url: Mapped[str | None] = mapped_column(String(500))
    carga_max_horas: Mapped[int] = mapped_column(Integer, default=0)
    area_principal: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    totp_secret: Mapped[str | None] = mapped_column(String(500))
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
