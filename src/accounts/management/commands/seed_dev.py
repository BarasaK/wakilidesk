from __future__ import annotations

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from clients.models import Client
from clients.services import create_client
from documents.models import Document
from documents.services import create_document_with_version, ensure_default_document_categories
from firms.models import Firm, FirmMembership
from firms.services import ensure_default_roles_for_firm
from matters.models import Matter, MatterParty
from matters.services import create_matter, ensure_default_practice_areas
from notifications.services import notify_user
from physical_files.models import PhysicalFile
from physical_files.services import create_physical_file, ensure_default_storage_locations


SEED_PASSWORD = "ChangeMe123!"

FIRM_SPECS = [
    {
        "name": "Amani & Co Advocates LLP",
        "display_name": "Amani Advocates",
        "slug": "amani-advocates",
        "email": "admin@amani.test",
        "accent_color": "#0f766e",
    },
    {
        "name": "Baraka Legal Partners",
        "display_name": "Baraka Legal",
        "slug": "baraka-legal",
        "email": "admin@baraka.test",
        "accent_color": "#1d4ed8",
    },
    {
        "name": "Kosmas Law Advocates LLP",
        "display_name": "Kosmas Law",
        "slug": "kosmaslaw",
        "email": "admin@kosmaslaw.test",
        "accent_color": "#7c2d12",
    },
]

ROLE_USERS = [
    ("Firm Administrator", "admin"),
    ("Partner", "partner"),
    ("Advocate", "advocate1"),
    ("Advocate", "advocate2"),
    ("Secretary", "secretary"),
    ("Clerk / Records Officer", "clerk"),
]

CLIENT_SPECS = [
    {
        "client_type": Client.ClientType.INDIVIDUAL,
        "name": "Jane Wanjiku",
        "email": "jane.wanjiku",
        "phone": "+254700100100",
        "address": "Westlands, Nairobi",
    },
    {
        "client_type": Client.ClientType.ORGANISATION,
        "name": "Mawingu Holdings Ltd",
        "email": "legal.mawingu",
        "phone": "+254711200200",
        "address": "Upper Hill, Nairobi",
        "company_registration_number": "CPR/2026/01842",
        "kra_pin": "P052600001K",
    },
    {
        "client_type": Client.ClientType.INDIVIDUAL,
        "name": "Peter Otieno",
        "email": "peter.otieno",
        "phone": "+254722300300",
        "address": "Mombasa Road, Nairobi",
    },
]

MATTER_SPECS = [
    {
        "client": "Jane Wanjiku",
        "title": "Employment Claim",
        "description": "Wrongful termination claim and settlement correspondence.",
        "practice_area_code": "EMP",
        "opened_date": "2026-08-21",
        "parties": [
            ("OPPOSING_PARTY", "Rift Valley Foods Ltd"),
            ("WITNESS", "Grace Akinyi"),
        ],
        "documents": [
            ("Client Instructions", "Employment Instructions", "EMP-INST-001"),
            ("Correspondence", "Demand Letter Draft", "EMP-COR-001"),
        ],
    },
    {
        "client": "Mawingu Holdings Ltd",
        "title": "Commercial Lease Review",
        "description": "Review of office lease, rent escalation, and exit clauses.",
        "practice_area_code": "CON",
        "opened_date": "2026-08-24",
        "parties": [
            ("OPPOSING_PARTY", "Greenfield Properties Ltd"),
            ("INTERESTED_PARTY", "Mawingu Finance Team"),
        ],
        "documents": [
            ("Agreements", "Lease Agreement Markup", "LEASE-AGR-001"),
            ("Research", "Lease Risk Note", "LEASE-RES-001"),
        ],
    },
    {
        "client": "Peter Otieno",
        "title": "Shareholders Agreement",
        "description": "Shareholder rights, reserved matters, and transfer restrictions.",
        "practice_area_code": "COR",
        "opened_date": "2026-08-27",
        "parties": [
            ("COMPANY_DIRECTOR", "Alice Njeri"),
            ("COMPANY_DIRECTOR", "David Kariuki"),
        ],
        "documents": [
            ("Agreements", "Shareholders Agreement Draft", "SHA-AGR-001"),
            ("Internal Notes", "Transaction Checklist", "SHA-NOTE-001"),
        ],
    },
]


class Command(BaseCommand):
    help = "Create example law firms, users, and rich dummy content for local development."

    @transaction.atomic
    def handle(self, *args, **options):
        seeded_firms = []
        for spec in FIRM_SPECS:
            context = self._seed_firm(spec)
            self._seed_users(context)
            self._seed_dummy_content(context)
            seeded_firms.append(context["firm"])

        self.stdout.write(self.style.SUCCESS("Seed data created."))
        self.stdout.write(f"Password for all seeded users: {SEED_PASSWORD}")
        self.stdout.write("Example accounts:")
        for firm in seeded_firms:
            domain = firm.slug.replace("-", "")
            self.stdout.write(f"  {firm.display_name}: admin@{domain}.test")

    def _seed_firm(self, spec):
        firm, _ = Firm.objects.update_or_create(
            slug=spec["slug"],
            defaults={
                "name": spec["name"],
                "display_name": spec["display_name"],
                "email": spec["email"],
                "country": "Kenya",
                "timezone": "Africa/Nairobi",
                "currency": "KES",
                "accent_color": spec["accent_color"],
                "is_active": True,
            },
        )
        return {
            "firm": firm,
            "roles": ensure_default_roles_for_firm(firm),
            "practice_areas": {area.code: area for area in ensure_default_practice_areas(firm)},
            "document_categories": {
                category.name: category for category in ensure_default_document_categories(firm)
            },
            "storage_locations": ensure_default_storage_locations(firm),
            "users": {},
        }

    def _seed_users(self, context):
        firm = context["firm"]
        domain = firm.slug.replace("-", "")
        for role_name, local_part in ROLE_USERS:
            email = f"{local_part}@{domain}.test"
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "username": email,
                    "first_name": local_part.replace("advocate", "advocate ").title(),
                    "last_name": firm.display_name.split()[0],
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
                    "role": context["roles"][role_name],
                    "status": FirmMembership.Status.ACTIVE,
                },
            )
            context["users"][local_part] = user

    def _seed_dummy_content(self, context):
        firm = context["firm"]
        admin_user = context["users"]["admin"]
        partner_user = context["users"]["partner"]
        advocate_user = context["users"]["advocate1"]
        domain = firm.slug.replace("-", "")
        clients = {}

        for spec in CLIENT_SPECS:
            client = Client.objects.filter(firm=firm, name=spec["name"]).first()
            if client is None:
                client = create_client(
                    firm=firm,
                    user=admin_user,
                    data={
                        **spec,
                        "email": f"{spec['email']}@{domain}.test",
                        "status": Client.Status.ACTIVE,
                    },
                )
            clients[spec["name"]] = client

        for index, spec in enumerate(MATTER_SPECS, start=1):
            client = clients[spec["client"]]
            practice_area = context["practice_areas"][spec["practice_area_code"]]
            matter = Matter.objects.filter(firm=firm, client=client, title=spec["title"]).first()
            if matter is None:
                matter = create_matter(
                    firm=firm,
                    user=admin_user,
                    data={
                        "client": client,
                        "title": spec["title"],
                        "description": spec["description"],
                        "practice_area": practice_area,
                        "status": Matter.Status.OPEN,
                        "responsible_partner": partner_user,
                        "responsible_advocate": advocate_user,
                        "opened_date": spec["opened_date"],
                        "closed_date": None,
                        "physical_file_exists": True,
                        "confidentiality_level": Matter.ConfidentialityLevel.STANDARD,
                    },
                )
            self._seed_matter_parties(firm, matter, spec["parties"], domain)
            self._seed_documents(context, matter, spec, admin_user)
            self._seed_physical_file(context, matter, index)

        if not firm.notifications.filter(recipient=admin_user, title="Development data ready").exists():
            notify_user(
                firm=firm,
                recipient=admin_user,
                title="Development data ready",
                message="Demo clients, matters, documents, and physical files are available for testing.",
                object_type="Firm",
                object_id=firm.id,
            )

    def _seed_matter_parties(self, firm, matter, party_specs, domain):
        for party_type, name in party_specs:
            MatterParty.objects.get_or_create(
                firm=firm,
                matter=matter,
                party_type=party_type,
                name=name,
                defaults={
                    "email": f"{name.lower().replace(' ', '.')}@{domain}.test",
                    "notes": "Seed party for development workflows.",
                },
            )

    def _seed_documents(self, context, matter, matter_spec, admin_user):
        firm = context["firm"]
        for category_name, title, reference_number in matter_spec["documents"]:
            if Document.objects.filter(firm=firm, matter=matter, title=title).exists():
                continue
            body = (
                f"{title}\n\n"
                f"Matter: {matter.title}\n"
                f"Client: {matter.client.name}\n"
                f"Reference: {reference_number}\n\n"
                "This is seeded dummy content for local development and search testing.\n"
            )
            create_document_with_version(
                firm=firm,
                user=admin_user,
                data={
                    "matter": matter,
                    "title": title,
                    "document_type": context["document_categories"][category_name],
                    "document_date": matter_spec["opened_date"],
                    "reference_number": reference_number,
                    "description": f"Seed {category_name.lower()} document.",
                    "source": Document.Source.INTERNAL_UPLOAD,
                    "confidentiality_level": Document.ConfidentialityLevel.STANDARD,
                },
                uploaded_file=ContentFile(
                    body.encode("utf-8"),
                    name=f"{title.lower().replace(' ', '-')}.txt",
                ),
            )

    def _seed_physical_file(self, context, matter, index):
        firm = context["firm"]
        file_number = f"PF-{firm.slug.upper()}-{index:04d}"
        if PhysicalFile.objects.filter(
            firm=firm,
            physical_file_number=file_number,
            volume_number=1,
        ).exists():
            return
        create_physical_file(
            firm=firm,
            data={
                "matter": matter,
                "physical_file_number": file_number,
                "volume_number": 1,
                "storage_location": context["storage_locations"][-1],
                "status": PhysicalFile.Status.IN_STORAGE,
                "digitisation_status": PhysicalFile.DigitisationStatus.NOT_STARTED,
                "barcode_or_qr_code": f"WD-{firm.slug.upper()}-{index:04d}",
                "notes": "Seed physical file linked to dummy matter.",
            },
        )
