from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from zoneinfo import ZoneInfo

import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.core.config import settings
from app.models.inscripcion import ConfiguracionInscripcion
from app.models.pago import Cargo, Pago
from app.models.sede import Sede
from app.models.student import Student
from app.services.inscripcion import pase_url


def _local_datetime(value: datetime | None) -> str:
    if value is None:
        return "-"
    local = value.astimezone(ZoneInfo(settings.APP_TIMEZONE))
    return local.strftime("%d/%m/%Y %H:%M")


def _money(value: Decimal | float | int, currency: str = "MXN") -> str:
    return f"${Decimal(str(value)):,.2f} {currency}"


def _truncate(value: str | None, limit: int = 70) -> str:
    text = value or "-"
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _draw_qr(pdf: canvas.Canvas, data: str, x: float, y: float, size: float = 108) -> None:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=1,
        border=1,
    )
    qr.add_data(data)
    qr.make(fit=True)
    matrix = qr.get_matrix()
    cells = len(matrix)
    cell = size / cells
    pdf.setFillColorRGB(0, 0, 0)
    for row_index, row in enumerate(matrix):
        for col_index, filled in enumerate(row):
            if not filled:
                continue
            pdf.rect(
                x + col_index * cell,
                y + (cells - row_index - 1) * cell,
                cell,
                cell,
                stroke=0,
                fill=1,
            )


def _header(pdf: canvas.Canvas, title: str, subtitle: str) -> None:
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(54, 738, title)
    pdf.setFont("Helvetica", 11)
    pdf.drawString(54, 719, subtitle)
    pdf.setStrokeColorRGB(0.72, 0.16, 0.16)
    pdf.setLineWidth(2)
    pdf.line(54, 709, 558, 709)


def build_pase_pdf(
    student: Student,
    sede: Sede | None,
    config: ConfiguracionInscripcion,
) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    _header(pdf, "CUEP · Pase de inscripción", f"Proceso {config.anio}")

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(54, 674, _truncate(student.full_name, 48))
    pdf.setFont("Helvetica", 11)
    pdf.drawString(54, 655, f"Matrícula: {student.matricula or '-'}")
    pdf.drawString(54, 639, f"Sede: {sede.nombre if sede else '-'}")
    pdf.drawString(54, 623, f"Nivel: {student.nivel}")
    pdf.drawString(54, 607, f"Estatus: {student.estatus}")
    pdf.drawString(54, 591, f"Correo: {_truncate(student.email, 52)}")
    pdf.drawString(54, 575, f"Teléfono: {student.phone or '-'}")

    qr_data = pase_url(student.qr_token) or student.qr_token or ""
    if qr_data:
        _draw_qr(pdf, qr_data, 390, 580, 150)
        pdf.setFont("Helvetica", 8)
        pdf.drawString(390, 565, "Presenta este código en la sede.")

    pdf.setFillColorRGB(0.95, 0.96, 0.97)
    pdf.roundRect(54, 400, 504, 130, 10, stroke=0, fill=1)
    pdf.setFillColorRGB(0.1, 0.1, 0.1)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(70, 508, "Instrucciones")
    pdf.setFont("Helvetica", 10)
    lines = [
        "1. Llega a la sede en el horario indicado por el personal.",
        "2. Muestra este pase impreso o desde tu teléfono.",
        "3. El check-in se realiza una sola vez y confirma tu asistencia.",
        "4. Conserva tu matrícula: es tu identificador durante el proceso.",
    ]
    for index, line in enumerate(lines):
        pdf.drawString(70, 487 - index * 18, line)

    pdf.setFont("Helvetica", 8)
    pdf.setFillColorRGB(0.45, 0.45, 0.45)
    pdf.drawString(54, 60, "Documento generado por el sistema CUEP. No válido como comprobante fiscal.")
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def build_recibo_pdf(
    pago: Pago,
    cargo: Cargo,
    student: Student,
    sede: Sede | None,
) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    _header(pdf, "CUEP · Recibo de pago", pago.recibo_codigo or f"Pago #{pago.id}")

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(54, 672, _truncate(student.full_name, 50))
    pdf.setFont("Helvetica", 11)
    pdf.drawString(54, 653, f"Matrícula: {student.matricula or '-'}")
    pdf.drawString(54, 637, f"Sede: {sede.nombre if sede else '-'}")
    pdf.drawString(54, 621, f"Concepto: {cargo.concepto}")
    pdf.drawString(54, 605, f"Método: {pago.metodo}")
    pdf.drawString(54, 589, f"Referencia: {pago.referencia or '-'}")
    pdf.drawString(54, 573, f"Fecha de pago: {_local_datetime(pago.fecha_pago)}")
    pdf.drawString(54, 557, f"Validado: {_local_datetime(pago.validado_at)}")

    pdf.setFillColorRGB(0.95, 0.96, 0.97)
    pdf.roundRect(54, 420, 504, 100, 10, stroke=0, fill=1)
    pdf.setFillColorRGB(0.1, 0.1, 0.1)
    pdf.setFont("Helvetica", 11)
    pdf.drawString(70, 490, "Monto pagado")
    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawString(70, 450, _money(pago.monto, pago.moneda))
    pdf.setFont("Helvetica", 10)
    pdf.drawString(340, 490, f"Estado: {pago.estado}")

    if pago.recibo_codigo:
        _draw_qr(pdf, pago.recibo_codigo, 390, 220, 140)
        pdf.setFont("Helvetica", 8)
        pdf.drawString(390, 205, "Código de recibo")

    pdf.setFont("Helvetica", 8)
    pdf.setFillColorRGB(0.45, 0.45, 0.45)
    pdf.drawString(
        54,
        60,
        f"Documento interno CUEP generado el {date.today().strftime('%d/%m/%Y')}. No válido como comprobante fiscal.",
    )
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
