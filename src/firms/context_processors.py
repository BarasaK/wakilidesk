from __future__ import annotations

from firms.models import FirmMembership


def current_firm_permissions(request):
    firm = getattr(request, "current_firm", None)
    if not request.user.is_authenticated or firm is None:
        return {"firm_permissions": set()}
    if request.user.is_superuser:
        permissions = set(
            FirmMembership.objects.filter(firm=firm)
            .values_list("role__permissions__codename", flat=True)
            .distinct()
        )
        permissions.update(
            {
                "manage_users",
                "manage_roles",
                "manage_firm_settings",
                "view_audit_logs",
                "view_client",
                "create_client",
                "edit_client",
                "view_matter",
                "create_matter",
                "edit_matter",
                "manage_confidential_matter",
                "view_document",
                "upload_document",
                "download_document",
                "edit_document_metadata",
                "create_document_version",
                "archive_document",
                "restore_document",
                "view_physical_file",
                "create_physical_file",
                "checkout_physical_file",
                "checkin_physical_file",
                "change_storage_location",
                "view_diaryevent",
                "create_diaryevent",
                "edit_diaryevent",
                "delete_diaryevent",
                "manage_diary_reminders",
            }
        )
        return {"firm_permissions": permissions}
    permissions = set(
        FirmMembership.objects.filter(
            user=request.user,
            firm=firm,
            status=FirmMembership.Status.ACTIVE,
        )
        .values_list("role__permissions__codename", flat=True)
        .distinct()
    )
    return {"firm_permissions": permissions}
