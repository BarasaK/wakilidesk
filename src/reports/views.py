from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render

from reports.forms import ReportRequestForm
from reports.services import (
    available_report_entities,
    build_report,
    csv_response,
    pdf_response,
    user_can_report_entity,
    xlsx_response,
)


@login_required
def report_index(request):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    form = ReportRequestForm()
    form.fields["entity"].choices = available_report_entities(firm=firm, user=request.user)
    return render(request, "reports/index.html", {"firm": firm, "form": form})


@login_required
def report_export(request):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    form = ReportRequestForm(request.GET or None)
    if not form.is_valid():
        form.fields["entity"].choices = available_report_entities(firm=firm, user=request.user)
        return render(request, "reports/index.html", {"firm": firm, "form": form}, status=400)

    entity = form.cleaned_data["entity"]
    export_format = form.cleaned_data["export_format"]
    if not user_can_report_entity(firm=firm, user=request.user, entity=entity):
        raise PermissionDenied("You do not have permission to export this report.")
    report = build_report(firm=firm, user=request.user, entity=entity)
    if export_format == "csv":
        return csv_response(report)
    if export_format == "xlsx":
        return xlsx_response(report)
    return pdf_response(firm=firm, report=report)


def _require_current_firm(request):
    return request.current_firm
