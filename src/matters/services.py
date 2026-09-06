from __future__ import annotations

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import ProtectedError, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from audit.services import record_audit_event
from firms.services import user_has_firm_permission
from matters.models import Matter, MatterParty, PracticeArea


def matters_for_firm(firm):
    return Matter.objects.filter(
        firm=firm,
        client__deleted_at__isnull=True,
        deleted_at__isnull=True,
    ).select_related("client", "practice_area")


def trashed_matters_for_firm(firm):
    return (
        Matter.objects.filter(firm=firm, deleted_at__isnull=False)
        .select_related("client", "practice_area")
        .order_by("-deleted_at", "matter_number")
    )


def matters_visible_to_user(*, firm, user):
    queryset = matters_for_firm(firm)
    if user_has_firm_permission(user, firm, "manage_confidential_matter"):
        return queryset
    return queryset.filter(
        Q(confidentiality_level=Matter.ConfidentialityLevel.STANDARD)
        | Q(responsible_partner=user)
        | Q(responsible_advocate=user)
    )


def user_can_access_matter(*, matter: Matter, firm, user) -> bool:
    if matter.firm_id != firm.id:
        return False
    return matters_visible_to_user(firm=firm, user=user).filter(id=matter.id).exists()


def get_matter_for_firm_or_404(firm, matter_id):
    return get_object_or_404(matters_for_firm(firm), id=matter_id)


def get_matter_for_user_or_404(*, firm, user, matter_id):
    return get_object_or_404(matters_visible_to_user(firm=firm, user=user), id=matter_id)


def get_trashed_matter_for_firm_or_404(firm, matter_id):
    return get_object_or_404(trashed_matters_for_firm(firm), id=matter_id)


def require_matter_access(*, matter: Matter, firm, user) -> None:
    if not user_can_access_matter(matter=matter, firm=firm, user=user):
        raise PermissionDenied("You do not have access to this matter.")


@transaction.atomic
def create_matter(*, firm, user, data, request=None) -> Matter:
    client = data["client"]
    if client.firm_id != firm.id or client.deleted_at is not None:
        raise ValueError("Client does not belong to the current firm.")
    practice_area = data.get("practice_area")
    if practice_area is not None and practice_area.firm_id != firm.id:
        raise ValueError("Practice area does not belong to the current firm.")
    require_confidentiality_permission(
        firm=firm,
        user=user,
        confidentiality_level=data["confidentiality_level"],
    )
    matter = Matter.objects.create(
        firm=firm,
        created_by=user,
        matter_number=next_matter_number(firm, practice_area),
        **data,
    )
    record_audit_event(
        request=request,
        firm=firm,
        user=user,
        action="matter_created",
        object_type="Matter",
        object_id=matter.id,
    )
    return matter


@transaction.atomic
def update_matter(*, matter: Matter, data, request=None) -> Matter:
    client = data["client"]
    if client.firm_id != matter.firm_id or client.deleted_at is not None:
        raise ValueError("Client does not belong to the current firm.")
    practice_area = data.get("practice_area")
    if practice_area is not None and practice_area.firm_id != matter.firm_id:
        raise ValueError("Practice area does not belong to the current firm.")
    user = request.user if request is not None else None
    if user is not None and data["confidentiality_level"] != matter.confidentiality_level:
        require_confidentiality_permission(
            firm=matter.firm,
            user=user,
            confidentiality_level=data["confidentiality_level"],
        )
    for field, value in data.items():
        setattr(matter, field, value)
    matter.save()
    record_audit_event(
        request=request,
        firm=matter.firm,
        action="matter_updated",
        object_type="Matter",
        object_id=matter.id,
    )
    return matter


@transaction.atomic
def create_matter_party(*, firm, matter: Matter, data, request=None) -> MatterParty:
    party = MatterParty.objects.create(firm=firm, matter=matter, **data)
    record_audit_event(
        request=request,
        firm=firm,
        action="matter_party_created",
        object_type="MatterParty",
        object_id=party.id,
    )
    return party


@transaction.atomic
def trash_matter(*, matter: Matter, request=None) -> Matter:
    matter.deleted_at = timezone.now()
    matter.save(update_fields=["deleted_at", "updated_at"])
    record_audit_event(
        request=request,
        firm=matter.firm,
        action="matter_moved_to_trash",
        object_type="Matter",
        object_id=matter.id,
    )
    return matter


@transaction.atomic
def restore_trashed_matter(*, matter: Matter, request=None) -> Matter:
    if matter.client.deleted_at is not None:
        raise ValueError("Matter cannot be restored while its client is still in trash.")
    matter.deleted_at = None
    matter.save(update_fields=["deleted_at", "updated_at"])
    record_audit_event(
        request=request,
        firm=matter.firm,
        action="matter_restored_from_trash",
        object_type="Matter",
        object_id=matter.id,
    )
    return matter


@transaction.atomic
def permanently_delete_matter(*, matter: Matter, request=None) -> None:
    firm = matter.firm
    matter_id = matter.id
    try:
        matter.delete()
    except ProtectedError as exc:
        raise ValueError("Matter cannot be permanently deleted while linked physical files exist.") from exc
    record_audit_event(
        request=request,
        firm=firm,
        action="matter_permanently_deleted",
        object_type="Matter",
        object_id=matter_id,
    )


def require_confidentiality_permission(*, firm, user, confidentiality_level: str) -> None:
    if confidentiality_level == Matter.ConfidentialityLevel.STANDARD:
        return
    if not user_has_firm_permission(user, firm, "manage_confidential_matter"):
        raise PermissionDenied("You do not have permission to mark matters confidential.")


def ensure_default_practice_areas(firm) -> list[PracticeArea]:
    defaults = [
        ("Litigation", "LIT"),
        ("Conveyancing", "CON"),
        ("Corporate & Commercial", "COR"),
        ("Employment", "EMP"),
        ("Family", "FAM"),
        ("Probate & Succession", "PRO"),
        ("Debt Recovery", "DEB"),
        ("Intellectual Property", "IP"),
        ("Tax", "TAX"),
        ("Arbitration", "ARB"),
    ]
    areas = []
    for name, code in defaults:
        area, _ = PracticeArea.objects.get_or_create(
            firm=firm,
            code=code,
            defaults={"name": name, "is_active": True},
        )
        areas.append(area)
    return areas


def next_matter_number(firm, practice_area=None) -> str:
    code = practice_area.code if practice_area else "GEN"
    year = timezone.localdate().year
    sequence = Matter.objects.filter(
        firm=firm,
        opened_date__year=year,
        practice_area=practice_area,
    ).count() + 1
    return firm.file_number_pattern.format(
        PRACTICE_AREA=code,
        YEAR=year,
        SEQUENCE=f"{sequence:05d}",
    )
