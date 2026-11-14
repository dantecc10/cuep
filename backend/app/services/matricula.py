from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sede import Sede
from app.models.student import Student
from app.services.normalization import initial


async def generar_matricula(db: AsyncSession, student: Student, sede: Sede) -> str:
    codigo = (sede.codigo or "").strip().upper()
    if not codigo or len(codigo) != 1 or not codigo.isalnum():
        raise ValueError("La sede no tiene código de matrícula configurado")

    nivel_code = "P" if student.nivel == "PREPA" else "L"

    result = await db.execute(text("SELECT nextval('student_folio_seq')"))
    folio = int(result.scalar_one())
    if folio > 9999:
        raise ValueError("Se alcanzó el límite de folios")

    iniciales = (
        initial(student.first_name or student.full_name)
        + initial(student.paternal_last_name)
        + initial(student.maternal_last_name)
    )

    matricula = f"{codigo}{nivel_code}{folio:04d}{iniciales}"
    student.folio = folio
    student.matricula = matricula
    await db.flush()
    return matricula
