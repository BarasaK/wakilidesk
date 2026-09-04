from __future__ import annotations

import csv
import html
import io
import zipfile
from dataclasses import dataclass

from django.http import HttpResponse
from django.utils import timezone

from clients.models import Client
from diary.services import diary_events_visible_to_user
from documents.services import documents_visible_to_user
from firms.services import user_has_firm_permission
from matters.services import matters_visible_to_user
from physical_files.services import physical_files_visible_to_user


@dataclass(frozen=True)
class ReportData:
    title: str
    filename: str
    headers: list[str]
    rows: list[list[str]]


def build_report(*, firm, user, entity: str) -> ReportData:
    builders = {
        "clients": _client_report,
        "matters": _matter_report,
        "documents": _document_report,
        "physical_files": _physical_file_report,
        "diary_events": _diary_event_report,
    }
    if entity not in builders:
        raise ValueError("Unknown report entity.")
    return builders[entity](firm=firm, user=user)


def user_can_report_entity(*, firm, user, entity: str) -> bool:
    permission_map = {
        "clients": "view_client",
        "matters": "view_matter",
        "documents": "view_document",
        "physical_files": "view_physical_file",
        "diary_events": "view_diaryevent",
    }
    codename = permission_map.get(entity)
    return bool(codename and user_has_firm_permission(user, firm, codename))


def available_report_entities(*, firm, user):
    choices = []
    for entity, label in (
        ("clients", "Clients"),
        ("matters", "Matters"),
        ("documents", "Documents"),
        ("physical_files", "Physical files"),
        ("diary_events", "Diary events"),
    ):
        if user_can_report_entity(firm=firm, user=user, entity=entity):
            choices.append((entity, label))
    return choices


def csv_response(report: ReportData) -> HttpResponse:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(report.headers)
    writer.writerows(report.rows)
    response = HttpResponse(output.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{report.filename}.csv"'
    return response


def xlsx_response(report: ReportData) -> HttpResponse:
    content = _xlsx_bytes(report)
    response = HttpResponse(
        content,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{report.filename}.xlsx"'
    return response


def pdf_response(*, firm, report: ReportData) -> HttpResponse:
    content = _pdf_bytes(firm=firm, report=report)
    response = HttpResponse(content, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{report.filename}.pdf"'
    return response


def _client_report(*, firm, user) -> ReportData:
    rows = [
        [
            client.client_number,
            client.name,
            client.get_client_type_display(),
            client.email,
            client.phone,
            client.get_status_display(),
            _format_datetime(client.created_at),
        ]
        for client in Client.objects.filter(firm=firm).order_by("name")
    ]
    return ReportData(
        title="Clients Report",
        filename="clients-report",
        headers=["Client Number", "Name", "Type", "Email", "Phone", "Status", "Created"],
        rows=rows,
    )


def _matter_report(*, firm, user) -> ReportData:
    rows = [
        [
            matter.matter_number,
            matter.title,
            matter.client.name,
            matter.practice_area.name if matter.practice_area else "",
            matter.get_status_display(),
            matter.get_confidentiality_level_display(),
            matter.responsible_partner.email if matter.responsible_partner else "",
            matter.responsible_advocate.email if matter.responsible_advocate else "",
            str(matter.opened_date),
        ]
        for matter in matters_visible_to_user(firm=firm, user=user).select_related(
            "client",
            "practice_area",
            "responsible_partner",
            "responsible_advocate",
        )
    ]
    return ReportData(
        title="Matters Report",
        filename="matters-report",
        headers=[
            "Matter Number",
            "Title",
            "Client",
            "Practice Area",
            "Status",
            "Confidentiality",
            "Partner",
            "Advocate",
            "Opened",
        ],
        rows=rows,
    )


def _document_report(*, firm, user) -> ReportData:
    rows = [
        [
            document.title,
            document.matter.matter_number,
            document.document_type.name,
            document.reference_number,
            str(document.document_date or ""),
            document.get_source_display(),
            document.get_confidentiality_level_display(),
            str(document.current_version.version_number) if document.current_version else "",
            "Archived" if document.archived_at else "Active",
        ]
        for document in documents_visible_to_user(firm=firm, user=user).select_related(
            "matter",
            "document_type",
            "current_version",
        )
    ]
    return ReportData(
        title="Documents Report",
        filename="documents-report",
        headers=[
            "Title",
            "Matter",
            "Category",
            "Reference",
            "Date",
            "Source",
            "Confidentiality",
            "Current Version",
            "Status",
        ],
        rows=rows,
    )


def _physical_file_report(*, firm, user) -> ReportData:
    rows = [
        [
            physical_file.physical_file_number,
            str(physical_file.volume_number),
            physical_file.matter.matter_number,
            str(physical_file.storage_location or ""),
            physical_file.get_status_display(),
            physical_file.get_digitisation_status_display(),
            physical_file.barcode_or_qr_code,
        ]
        for physical_file in physical_files_visible_to_user(firm=firm, user=user).select_related(
            "matter",
            "storage_location",
        )
    ]
    return ReportData(
        title="Physical Files Report",
        filename="physical-files-report",
        headers=[
            "File Number",
            "Volume",
            "Matter",
            "Location",
            "Status",
            "Digitisation",
            "Barcode/QR",
        ],
        rows=rows,
    )


def _diary_event_report(*, firm, user) -> ReportData:
    rows = [
        [
            event.title,
            event.get_event_type_display(),
            _format_datetime(event.start_at),
            _format_datetime(event.end_at) if event.end_at else "",
            event.matter.matter_number if event.matter else "",
            event.court_name,
            event.location,
            event.assigned_to.email if event.assigned_to else "",
            event.get_status_display(),
        ]
        for event in diary_events_visible_to_user(firm=firm, user=user).select_related(
            "matter",
            "assigned_to",
        )
    ]
    return ReportData(
        title="Diary Events Report",
        filename="diary-events-report",
        headers=[
            "Title",
            "Type",
            "Start",
            "End",
            "Matter",
            "Court",
            "Location",
            "Assigned To",
            "Status",
        ],
        rows=rows,
    )


def _format_datetime(value):
    return timezone.localtime(value).strftime("%Y-%m-%d %H:%M") if value else ""


def _xlsx_bytes(report: ReportData) -> bytes:
    rows = [report.headers, *report.rows]
    sheet_rows = "\n".join(
        f'<row r="{row_index}">'
        + "".join(
            f'<c r="{_column_letter(column_index)}{row_index}" t="inlineStr"><is><t>{_xml_escape(value)}</t></is></c>'
            for column_index, value in enumerate(row, start=1)
        )
        + "</row>"
        for row_index, row in enumerate(rows, start=1)
    )
    worksheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheetData>{sheet_rows}</sheetData>"
        "</worksheet>"
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _xlsx_content_types())
        archive.writestr("_rels/.rels", _xlsx_root_rels())
        archive.writestr("xl/workbook.xml", _xlsx_workbook())
        archive.writestr("xl/_rels/workbook.xml.rels", _xlsx_workbook_rels())
        archive.writestr("xl/worksheets/sheet1.xml", worksheet)
    return buffer.getvalue()


def _column_letter(index: int) -> str:
    letters = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def _xml_escape(value) -> str:
    return html.escape(str(value), quote=False)


def _xlsx_content_types() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        "</Types>"
    )


def _xlsx_root_rels() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>"
    )


def _xlsx_workbook() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Report" sheetId="1" r:id="rId1"/></sheets>'
        "</workbook>"
    )


def _xlsx_workbook_rels() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        "</Relationships>"
    )


def _pdf_bytes(*, firm, report: ReportData) -> bytes:
    lines = [
        firm.display_name,
        report.title,
        f"Generated: {_format_datetime(timezone.now())}",
        "",
        " | ".join(report.headers),
    ]
    for row in report.rows[:32]:
        lines.append(" | ".join(str(value) for value in row))
    if len(report.rows) > 32:
        lines.append(f"... {len(report.rows) - 32} additional rows omitted from PDF preview.")

    logo = _read_pdf_logo(firm)
    return _simple_pdf(lines=lines, logo=logo)


def _read_pdf_logo(firm):
    if not firm.logo:
        return None
    try:
        from PIL import Image

        with Image.open(firm.logo.path) as image:
            image.thumbnail((120, 60))
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=90)
            return {
                "width": image.width,
                "height": image.height,
                "data": buffer.getvalue(),
            }
    except Exception:
        return None


def _simple_pdf(*, lines, logo=None) -> bytes:
    objects = []
    content_lines = ["BT", "/F1 10 Tf", "50 780 Td", "14 TL"]
    if logo:
        content_lines = ["q", f"{logo['width']} 0 0 {logo['height']} 50 722 cm", "/Im1 Do", "Q", *content_lines]
    for line in lines:
        safe_line = str(line).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        content_lines.append(f"({safe_line[:130]}) Tj")
        content_lines.append("T*")
    content_lines.append("ET")
    content = "\n".join(content_lines).encode("latin-1", errors="replace")

    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    resources = b"<< /Font << /F1 4 0 R >>"
    if logo:
        resources += b" /XObject << /Im1 6 0 R >>"
    resources += b" >>"
    objects.append(
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources "
        + resources
        + b" /Contents 5 0 R >>"
    )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objects.append(b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream")
    if logo:
        objects.append(
            b"<< /Type /XObject /Subtype /Image /Width "
            + str(logo["width"]).encode()
            + b" /Height "
            + str(logo["height"]).encode()
            + b" /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length "
            + str(len(logo["data"])).encode()
            + b" >>\nstream\n"
            + logo["data"]
            + b"\nendstream"
        )

    buffer = io.BytesIO()
    buffer.write(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(buffer.tell())
        buffer.write(f"{index} 0 obj\n".encode())
        buffer.write(obj)
        buffer.write(b"\nendobj\n")
    xref_position = buffer.tell()
    buffer.write(f"xref\n0 {len(objects) + 1}\n".encode())
    buffer.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        buffer.write(f"{offset:010d} 00000 n \n".encode())
    buffer.write(
        b"trailer\n<< /Size "
        + str(len(objects) + 1).encode()
        + b" /Root 1 0 R >>\nstartxref\n"
        + str(xref_position).encode()
        + b"\n%%EOF"
    )
    return buffer.getvalue()
