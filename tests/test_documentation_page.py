import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_public_documentation_page_renders_end_user_manual(client):
    response = client.get(reverse("documentation"))

    assert response.status_code == 200
    assert b"wakiliDesk End User Manual" in response.content
    assert b"Use <strong>Reports</strong> to download summaries" in response.content
    assert b'class="mermaid"' in response.content
    assert b"Technical Architecture" not in response.content
