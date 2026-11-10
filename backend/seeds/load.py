import asyncio
import sys
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import async_session_factory
from app.core.security import get_password_hash
from app.models.materia import Materia
from app.models.sede import Sede
from app.models.user import User


async def main():
    async with async_session_factory() as session:
        existing_admin = await session.execute(select(User).where(User.email == "admin@example.com"))
        if existing_admin.scalar_one_or_none() is None:
            session.add(
                User(
                    email="admin@example.com",
                    password_hash=get_password_hash("admin123"),
                    nombre="Admin",
                    apellido_paterno="CUEP",
                    role="admin",
                    es_tutor=False,
                )
            )

        for nombre, nivel, area in [
            ("Pensamiento Matemático", "PREPA", "Exactas"),
            ("Lectura y Redacción", "PREPA", "Sociales"),
        ]:
            existing_materia = await session.execute(
                select(Materia).where(Materia.nombre == nombre, Materia.nivel == nivel)
            )
            if existing_materia.scalar_one_or_none() is None:
                session.add(Materia(nombre=nombre, nivel=nivel, area=area))

        existing_sede = await session.execute(select(Sede).where(Sede.nombre == "Sede Centro"))
        sede = existing_sede.scalar_one_or_none()
        if sede is None:
            session.add(
                Sede(
                    nombre="Sede Centro",
                    codigo="C",
                    ciudad="Puebla",
                    descripcion="Sede comunitaria del CUEP en el centro de Puebla.",
                )
            )
        elif not sede.codigo:
            sede.codigo = "C"

        await session.commit()
        print("seeded")


if __name__ == "__main__":
    asyncio.run(main())
