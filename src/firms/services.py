from __future__ import annotations

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from firms.models import Firm, FirmMembership, Permission, Role


DEFAULT_PERMISSIONS = {
    "Clients": ["view_client", "create_client", "edit_client", "archive_client"],
    "Matters": [
        "view_matter",
        "create_matter",
        "edit_matter",
        "close_matter",
        "view_all_matters",
        "manage_confidential_matter",
    ],
    "Documents": [
        "view_document",
        "upload_document",
        "download_document",
        "edit_document_metadata",
        "create_document_version",
        "archive_document",
        "delete_document",
        "restore_document",
        "bulk_upload_documents",
    ],
    "Physical Files": [
        "view_physical_file",
        "create_physical_file",
        "checkout_physical_file",
        "checkin_physical_file",
        "change_storage_location",
    ],
    "Administration": [
        "manage_users",
        "manage_roles",
        "manage_firm_settings",
        "view_audit_logs",
    ],
}

DEFAULT_ROLES = {
    "Firm Administrator": [permission for group in DEFAULT_PERMISSIONS.values() for permission in group],
    "Partner": [
        "view_client",
        "view_matter",
        "create_matter",
        "edit_matter",
        "view_all_matters",
        "manage_confidential_matter",
        "view_document",
        "upload_document",
        "download_document",
        "create_document_version",
        "view_physical_file",
    ],
    "Advocate": [
        "view_client",
        "view_matter",
        "create_matter",
        "edit_matter",
        "view_document",
        "upload_document",
        "download_document",
        "create_document_version",
    ],
    "Secretary": [
        "view_client",
        "create_client",
        "edit_client",
        "view_matter",
        "create_matter",
        "view_document",
        "upload_document",
        "edit_document_metadata",
        "view_physical_file",
    ],
    "Clerk / Records Officer": [
        "view_client",
        "view_matter",
        "view_document",
        "upload_document",
        "edit_document_metadata",
        "bulk_upload_documents",
        "view_physical_file",
        "create_physical_file",
        "checkout_physical_file",
        "checkin_physical_file",
        "change_storage_location",
    ],
    "Auditor / Read-only": [
        "view_client",
        "view_matter",
        "view_document",
        "download_document",
        "view_physical_file",
        "view_audit_logs",
    ],
    "Finance": [],
}


def ensure_default_permissions() -> dict[str, Permission]:
    permissions: dict[str, Permission] = {}
    for module, codenames in DEFAULT_PERMISSIONS.items():
        for codename in codenames:
            permission, _ = Permission.objects.get_or_create(
                codename=codename,
                defaults={
                    "module": module,
                    "name": codename.replace("_", " ").title(),
                },
            )
            permissions[codename] = permission
    return permissions


def ensure_default_roles_for_firm(firm: Firm) -> dict[str, Role]:
    permissions = ensure_default_permissions()
    roles: dict[str, Role] = {}
    for role_name, codenames in DEFAULT_ROLES.items():
        role, _ = Role.objects.get_or_create(
            firm=firm,
            name=role_name,
            defaults={"is_system_default": True},
        )
        role.permissions.set([permissions[codename] for codename in codenames])
        roles[role_name] = role
    return roles


def get_active_memberships_for_user(user):
    if not user.is_authenticated:
        return FirmMembership.objects.none()
    return FirmMembership.objects.filter(
        user=user,
        status=FirmMembership.Status.ACTIVE,
        firm__is_active=True,
    )


def user_can_access_firm(user, firm: Firm) -> bool:
    return get_active_memberships_for_user(user).filter(firm=firm).exists()


def get_firm_for_user_or_404(user, firm_id):
    firm = get_object_or_404(Firm, id=firm_id, is_active=True)
    if not user_can_access_firm(user, firm):
        raise PermissionDenied("You do not have access to this firm.")
    return firm


def user_has_firm_permission(user, firm: Firm, codename: str) -> bool:
    if user.is_superuser:
        return True
    return FirmMembership.objects.filter(
        user=user,
        firm=firm,
        status=FirmMembership.Status.ACTIVE,
        role__permissions__codename=codename,
    ).exists()


def require_firm_permission(user, firm: Firm, codename: str) -> None:
    if not user_has_firm_permission(user, firm, codename):
        raise PermissionDenied("You do not have permission for this action.")
