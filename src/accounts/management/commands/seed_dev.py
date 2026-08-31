from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from firms.models import Firm, FirmMembership
from firms.services import ensure_default_roles_for_firm


SEED_PASSWORD = "ChangeMe123!"


class Command(BaseCommand):
    help = "Create two example law firms, default roles, and development users."

    @transaction.atomic
    def handle(self, *args, **options):
        firm_specs = [
            {
                "name": "Amani & Co Advocates LLP",
                "display_name": "Amani Advocates",
                "slug": "amani-advocates",
                "email": "admin@amani.test",
            },
            {
                "name": "Baraka Legal Partners",
                "display_name": "Baraka Legal",
                "slug": "baraka-legal",
                "email": "admin@baraka.test",
            },
        ]

        role_users = [
            ("Firm Administrator", "admin"),
            ("Partner", "partner"),
            ("Advocate", "advocate1"),
            ("Advocate", "advocate2"),
            ("Secretary", "secretary"),
            ("Clerk / Records Officer", "clerk"),
        ]

        for spec in firm_specs:
            firm, _ = Firm.objects.update_or_create(
                slug=spec["slug"],
                defaults={
                    "name": spec["name"],
                    "display_name": spec["display_name"],
                    "email": spec["email"],
                    "country": "Kenya",
                    "timezone": "Africa/Nairobi",
                    "currency": "KES",
                    "is_active": True,
                },
            )
            roles = ensure_default_roles_for_firm(firm)
            domain = spec["slug"].replace("-", "")
            for role_name, local_part in role_users:
                email = f"{local_part}@{domain}.test"
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        "username": email,
                        "first_name": local_part.title(),
                        "last_name": spec["display_name"].split()[0],
                        "is_active": True,
                    },
                )
                if created:
                    user.set_password(SEED_PASSWORD)
                    user.save(update_fields=["password"])
                FirmMembership.objects.update_or_create(
                    user=user,
                    firm=firm,
                    defaults={
                        "role": roles[role_name],
                        "status": FirmMembership.Status.ACTIVE,
                    },
                )

        self.stdout.write(self.style.SUCCESS("Seed data created."))
        self.stdout.write(f"Password for all seeded users: {SEED_PASSWORD}")
        self.stdout.write("Example accounts:")
        self.stdout.write("  admin@amaniadvocates.test")
        self.stdout.write("  advocate1@amaniadvocates.test")
        self.stdout.write("  admin@barakalegal.test")
