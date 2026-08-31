from __future__ import annotations

from django.db.models import Q

from clients.models import Client
from documents.models import Document
from firms.services import user_has_firm_permission
from matters.models import Matter, MatterParty
from physical_files.models import PhysicalFile


def global_search(*, firm, user, query: str) -> dict[str, list]:
    query = query.strip()
    if not query:
        return {"clients": [], "matters": [], "documents": [], "physical_files": [], "parties": []}

    results = {"clients": [], "matters": [], "documents": [], "physical_files": [], "parties": []}

    if user_has_firm_permission(user, firm, "view_client"):
        results["clients"] = list(
            Client.objects.filter(firm=firm).filter(
                Q(name__icontains=query)
                | Q(client_number__icontains=query)
                | Q(email__icontains=query)
                | Q(phone__icontains=query)
            )[:20]
        )

    if user_has_firm_permission(user, firm, "view_matter"):
        results["matters"] = list(
            Matter.objects.filter(firm=firm).select_related("client", "practice_area").filter(
                Q(matter_number__icontains=query)
                | Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(client__name__icontains=query)
            )[:20]
        )
        results["parties"] = list(
            MatterParty.objects.filter(firm=firm).select_related("matter").filter(
                Q(name__icontains=query)
                | Q(email__icontains=query)
                | Q(phone__icontains=query)
            )[:20]
        )

    if user_has_firm_permission(user, firm, "view_document"):
        results["documents"] = list(
            Document.objects.filter(firm=firm, deleted_at__isnull=True)
            .select_related("matter", "document_type")
            .filter(
                Q(title__icontains=query)
                | Q(reference_number__icontains=query)
                | Q(description__icontains=query)
                | Q(versions__extracted_text__icontains=query)
            )
            .distinct()[:20]
        )

    if user_has_firm_permission(user, firm, "view_physical_file"):
        results["physical_files"] = list(
            PhysicalFile.objects.filter(firm=firm).select_related("matter", "storage_location").filter(
                Q(physical_file_number__icontains=query)
                | Q(barcode_or_qr_code__icontains=query)
                | Q(notes__icontains=query)
                | Q(matter__matter_number__icontains=query)
            )[:20]
        )

    return results
