from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from clients.services import create_client
from documents.services import create_document_with_version, ensure_default_document_categories
from django.core.files.base import ContentFile
from firms.models import Firm, FirmMembership
from firms.services import ensure_default_roles_for_firm
from matters.services import create_matter, ensure_default_practice_areas
from physical_files.services import create_physical_file, ensure_default_storage_locations


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
            practice_areas = ensure_default_practice_areas(firm)
            document_categories = ensure_default_document_categories(firm)
            storage_locations = ensure_default_storage_locations(firm)
            domain = spec["slug"].replace("-", "")
            admin_user = None
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
                if role_name == "Firm Administrator":
                    admin_user = user

            if admin_user and not firm.clients.exists():
                client = create_client(
                    firm=firm,
                    user=admin_user,
                    data={
                        "client_type": "INDIVIDUAL",
                        "name": f"{firm.display_name} Pilot Client",
                        "email": f"client@{domain}.test",
                        "phone": "+254700000000",
                        "address": "Nairobi",
                        "status": "ACTIVE",
                    },
                )
                matter = create_matter(
                    firm=firm,
                    user=admin_user,
                    data={
                        "client": client,
                        "title": "Pilot Matter",
                        "description": "Development matter for tenant isolation checks.",
                        "practice_area": practice_areas[0],
                        "status": "OPEN",
                        "responsible_partner": admin_user,
                        "responsible_advocate": admin_user,
                        "opened_date": "2026-08-31",
                        "closed_date": None,
                        "physical_file_exists": True,
                        "confidentiality_level": "STANDARD",
                    },
                )
                create_document_with_version(
                    firm=firm,
                    user=admin_user,
                    data={
                        "matter": matter,
                        "title": "Pilot Instructions",
                        "document_type": document_categories[0],
                        "document_date": "2026-08-31",
                        "reference_number": "PILOT-001",
                        "description": "Seed document for development.",
                        "source": "INTERNAL_UPLOAD",
                        "confidentiality_level": "STANDARD",
                    },
                    uploaded_file=ContentFile(b"Pilot instructions", name="pilot-instructions.txt"),
                )
                create_physical_file(
                    firm=firm,
                    data={
                        "matter": matter,
                        "physical_file_number": f"PF-{firm.slug.upper()}-0001",
                        "volume_number": 1,
                        "storage_location": storage_locations[-1],
                        "status": "IN_STORAGE",
                        "digitisation_status": "NOT_STARTED",
                        "barcode_or_qr_code": "",
                        "notes": "Seed physical file.",
                    },
                )

        self.stdout.write(self.style.SUCCESS("Seed data created."))
        self.stdout.write(f"Password for all seeded users: {SEED_PASSWORD}")
        self.stdout.write("Example accounts:")
        self.stdout.write("  admin@amaniadvocates.test")
        self.stdout.write("  advocate1@amaniadvocates.test")
        self.stdout.write("  admin@barakalegal.test")
