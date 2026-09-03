from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from diary.forms import DiaryEventFilterForm, DiaryEventForm
from diary.models import DiaryEvent
from diary.services import (
    create_diary_event,
    diary_events_visible_to_user,
    filter_diary_events,
    update_diary_event,
)
from firms.services import require_firm_permission


@login_required
def diary_event_list(request):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "view_diaryevent")
    form = DiaryEventFilterForm(request.GET or None, firm=firm)
    events = diary_events_visible_to_user(firm=firm, user=request.user)
    if form.is_valid():
        events = filter_diary_events(events, data=form.cleaned_data)
    upcoming_events = events.filter(
        status=DiaryEvent.Status.SCHEDULED,
        start_at__gte=timezone.now(),
    )[:8]
    overdue_events = events.filter(
        status=DiaryEvent.Status.SCHEDULED,
        start_at__lt=timezone.now(),
    ).order_by("-start_at")[:8]
    return render(
        request,
        "diary/list.html",
        {
            "firm": firm,
            "form": form,
            "events": events,
            "upcoming_events": upcoming_events,
            "overdue_events": overdue_events,
        },
    )


@login_required
def diary_event_create(request):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "create_diaryevent")
    if request.method == "POST":
        form = DiaryEventForm(request.POST, firm=firm, user=request.user)
        if form.is_valid():
            event = create_diary_event(
                firm=firm,
                user=request.user,
                data=_event_data(form),
                reminder_offsets=form.cleaned_data["reminder_offsets"],
                reminder_channels=form.cleaned_data["reminder_channels"],
                request=request,
            )
            messages.success(request, "Diary event created.")
            return redirect("diary_event_detail", event_id=event.id)
    else:
        form = DiaryEventForm(firm=firm, user=request.user)
    return render(request, "diary/form.html", {"firm": firm, "form": form})


@login_required
def diary_event_detail(request, event_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "view_diaryevent")
    event = get_object_or_404(
        diary_events_visible_to_user(firm=firm, user=request.user).prefetch_related("reminders"),
        id=event_id,
    )
    return render(request, "diary/detail.html", {"firm": firm, "event": event})


@login_required
def diary_event_edit(request, event_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "edit_diaryevent")
    event = get_object_or_404(
        diary_events_visible_to_user(firm=firm, user=request.user),
        id=event_id,
    )
    if request.method == "POST":
        form = DiaryEventForm(request.POST, firm=firm, user=request.user, instance=event)
        if form.is_valid():
            update_diary_event(
                event=event,
                user=request.user,
                data=_event_data(form),
                reminder_offsets=form.cleaned_data["reminder_offsets"],
                reminder_channels=form.cleaned_data["reminder_channels"],
                request=request,
            )
            messages.success(request, "Diary event updated.")
            return redirect("diary_event_detail", event_id=event.id)
    else:
        form = DiaryEventForm(firm=firm, user=request.user, instance=event)
    return render(request, "diary/form.html", {"firm": firm, "form": form, "event": event})


@login_required
def diary_event_status(request, event_id, status):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "edit_diaryevent")
    event = get_object_or_404(diary_events_visible_to_user(firm=firm, user=request.user), id=event_id)
    if request.method == "POST" and status in DiaryEvent.Status.values:
        event.status = status
        event.save(update_fields=["status"])
        messages.success(request, "Diary event status updated.")
    return redirect("diary_event_detail", event_id=event.id)


@login_required
def diary_event_delete(request, event_id):
    firm = _require_current_firm(request)
    if firm is None:
        return redirect("firm_onboarding")
    require_firm_permission(request.user, firm, "delete_diaryevent")
    event = get_object_or_404(diary_events_visible_to_user(firm=firm, user=request.user), id=event_id)
    if request.method == "POST":
        event.delete()
        messages.success(request, "Diary event deleted.")
        return redirect("diary_event_list")
    return render(request, "diary/delete.html", {"firm": firm, "event": event})


def _event_data(form):
    return {field: form.cleaned_data[field] for field in DiaryEventForm.Meta.fields}


def _require_current_firm(request):
    if request.current_firm is None:
        return None
    return request.current_firm
