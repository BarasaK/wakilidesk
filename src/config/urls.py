from django.contrib import admin
from django.conf import settings
from django.urls import include, path
from django.views.static import serve

from common.views import documentation, health
from firms import views as firm_views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
    path("documentation/", documentation, name="documentation"),
    path("accounts/", include("accounts.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("clients/", include("clients.urls")),
    path("matters/", include("matters.urls")),
    path("documents/", include("documents.urls")),
    path("physical-files/", include("physical_files.urls")),
    path("diary/", include("diary.urls")),
    path("notifications/", include("notifications.urls")),
    path("reports/", include("reports.urls")),
    path("search/", include("search.urls")),
    path("", firm_views.dashboard, name="dashboard"),
    path("onboarding/firm/", firm_views.firm_onboarding, name="firm_onboarding"),
    path("app/firm/profile/", firm_views.firm_profile, name="firm_profile"),
    path("app/administration/users/", firm_views.admin_users, name="admin_users"),
    path("app/administration/users/invite/", firm_views.invite_user, name="invite_user"),
    path("app/administration/roles/", firm_views.roles_list, name="roles_list"),
    path("app/administration/roles/new/", firm_views.role_create, name="role_create"),
    path("app/administration/roles/<uuid:role_id>/edit/", firm_views.role_edit, name="role_edit"),
    path("app/firms/<uuid:firm_id>/", firm_views.firm_detail, name="firm_detail"),
    path(
        "media/firm-logos/<path:path>",
        serve,
        {"document_root": settings.MEDIA_ROOT / "firm-logos"},
        name="firm_logo_media",
    ),
]
