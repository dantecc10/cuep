import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.core.database import async_session_factory
from app.core.security import get_password_hash
from app.models.user import User
from app.models.materia import Materia
from app.models.sede import Sede


async def main():
    async with async_session_factory() as session:
        admin = User(email="admin@example.com", password_hash=get_password_hash("admin123"), nombre="Admin", apellido_paterno="CUEP", role="admin", es_tutor=False)
        session.add(admin)
        session.add(Materia(nombre="Pensamiento Matemático", nivel="PREPA", area="Exactas"))
        session.add(Materia(nombre="Lectura y Redacción", nivel="PREPA", area="Sociales"))
        session.add(Sede(nombre="Sede Centro"))
        await session.commit()
        print("seeded")


if __name__ == "__main__":
    asyncio.run(main())
