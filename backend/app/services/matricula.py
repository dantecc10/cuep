from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sede import Sede
from app.models.student import Student


async def generar_matricula(db: AsyncSession, student: Student, sede: Sede) -> str:
    if not sede.codigo or len(sede.codigo) != 1:
        raise ValueError("La sede no tiene código de matrícula configurado")

    nivel_code = "P" if student.nivel == "PREPA" else "L"

    result = await db.execute(select(func.coalesce(func.max(Student.folio), 0)))
    folio = int(result.scalar() or 0) + 1
    if folio > 9999:
        raise ValueError("Se alcanzó el límite de folios")

    def inicial(valor: str | None) -> str:
        if not valor:
            return "X"
        return valor.strip()[0].upper()

    iniciales = (
        inicial(student.first_name or student.full_name)
        + inicial(student.paternal_last_name)
        + inicial(student.maternal_last_name)
    )

    matricula = f"{sede.codigo}{nivel_code}{folio:04d}{iniciales}"
    student.folio = folio
    student.matricula = matricula
    await db.flush()
    return matricula
