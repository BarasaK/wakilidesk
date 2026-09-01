import pytest
from django.core.management import call_command
from django.test import override_settings

from accounts.models import User
from clients.models import Client
from documents.models import Document
from firms.models import Firm, FirmMembership
from matters.models import Matter, MatterParty
from notifications.models import Notification
from physical_files.models import PhysicalFile


@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
def test_seed_dev_creates_kosmas_law_dummy_content_idempotently():
    call_command("seed_dev")

    firm = Firm.objects.get(slug="kosmaslaw")
    assert firm.display_name == "Kosmas Law"
    assert firm.accent_color == "#7c2d12"
    assert User.objects.filter(email="admin@kosmaslaw.test").exists()
    assert FirmMembership.objects.filter(firm=firm).count() == 6
    assert Client.objects.filter(firm=firm).count() == 3
    assert Matter.objects.filter(firm=firm).count() == 3
    assert MatterParty.objects.filter(firm=firm).count() == 6
    assert Document.objects.filter(firm=firm).count() == 6
    assert PhysicalFile.objects.filter(firm=firm).count() == 3
    assert Notification.objects.filter(firm=firm, title="Development data ready").count() == 1

    counts = {
        "clients": Client.objects.filter(firm=firm).count(),
        "matters": Matter.objects.filter(firm=firm).count(),
        "documents": Document.objects.filter(firm=firm).count(),
        "physical_files": PhysicalFile.objects.filter(firm=firm).count(),
        "notifications": Notification.objects.filter(firm=firm).count(),
    }

    call_command("seed_dev")

    assert Client.objects.filter(firm=firm).count() == counts["clients"]
    assert Matter.objects.filter(firm=firm).count() == counts["matters"]
    assert Document.objects.filter(firm=firm).count() == counts["documents"]
    assert PhysicalFile.objects.filter(firm=firm).count() == counts["physical_files"]
    assert Notification.objects.filter(firm=firm).count() == counts["notifications"]
