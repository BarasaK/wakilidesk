from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render

from common.markdown import render_markdown_document


def health(request):
    return JsonResponse({"status": "ok"})


def documentation(request):
    manual_path = settings.BASE_DIR / "docs" / "end-user-manual.md"
    manual = manual_path.read_text(encoding="utf-8")
    return render(
        request,
        "common/documentation.html",
        {"manual_html": render_markdown_document(manual)},
    )
