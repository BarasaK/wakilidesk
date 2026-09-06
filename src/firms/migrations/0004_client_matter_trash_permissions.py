from django.db import migrations


def add_trash_permissions(apps, schema_editor):
    Permission = apps.get_model("firms", "Permission")
    Role = apps.get_model("firms", "Role")

    permission_specs = {
        "delete_client": ("Delete Client", "Clients"),
        "restore_client": ("Restore Client", "Clients"),
        "delete_matter": ("Delete Matter", "Matters"),
        "restore_matter": ("Restore Matter", "Matters"),
    }
    permissions = []
    for codename, (name, module) in permission_specs.items():
        permission, _ = Permission.objects.get_or_create(
            codename=codename,
            defaults={"name": name, "module": module},
        )
        permissions.append(permission)

    for role in Role.objects.filter(name="Firm Administrator"):
        role.permissions.add(*permissions)


def remove_trash_permissions(apps, schema_editor):
    Permission = apps.get_model("firms", "Permission")
    Permission.objects.filter(
        codename__in=["delete_client", "restore_client", "delete_matter", "restore_matter"]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("firms", "0003_firm_accent_color"),
    ]

    operations = [
        migrations.RunPython(add_trash_permissions, remove_trash_permissions),
    ]
