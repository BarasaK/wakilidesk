from django.db import migrations


DIARY_PERMISSIONS = {
    "view_diaryevent": "View Diary Event",
    "create_diaryevent": "Create Diary Event",
    "edit_diaryevent": "Edit Diary Event",
    "delete_diaryevent": "Delete Diary Event",
    "manage_diary_reminders": "Manage Diary Reminders",
}

ROLE_PERMISSIONS = {
    "Firm Administrator": [
        "view_diaryevent",
        "create_diaryevent",
        "edit_diaryevent",
        "delete_diaryevent",
        "manage_diary_reminders",
    ],
    "Partner": [
        "view_diaryevent",
        "create_diaryevent",
        "edit_diaryevent",
        "manage_diary_reminders",
    ],
    "Advocate": [
        "view_diaryevent",
        "create_diaryevent",
        "edit_diaryevent",
    ],
    "Secretary": [
        "view_diaryevent",
        "create_diaryevent",
        "edit_diaryevent",
    ],
    "Clerk / Records Officer": ["view_diaryevent"],
    "Auditor / Read-only": ["view_diaryevent"],
}


def add_diary_permissions(apps, schema_editor):
    Permission = apps.get_model("firms", "Permission")
    Role = apps.get_model("firms", "Role")
    permissions = {}
    for codename, name in DIARY_PERMISSIONS.items():
        permission, _created = Permission.objects.get_or_create(
            codename=codename,
            defaults={
                "name": name,
                "module": "Diary",
                "description": "",
            },
        )
        permissions[codename] = permission

    for role_name, codenames in ROLE_PERMISSIONS.items():
        for role in Role.objects.filter(name=role_name):
            role.permissions.add(*[permissions[codename] for codename in codenames])


def remove_diary_permissions(apps, schema_editor):
    Permission = apps.get_model("firms", "Permission")
    Permission.objects.filter(codename__in=DIARY_PERMISSIONS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("diary", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(add_diary_permissions, remove_diary_permissions),
    ]
