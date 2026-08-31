from django.contrib import admin
from django.urls import include, path

from common.views import health
from firms import views as firm_views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
    path("accounts/", include("accounts.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", firm_views.dashboard, name="dashboard"),
    path("onboarding/firm/", firm_views.firm_onboarding, name="firm_onboarding"),
    path("app/firm/profile/", firm_views.firm_profile, name="firm_profile"),
    path("app/administration/users/", firm_views.admin_users, name="admin_users"),
    path("app/administration/users/invite/", firm_views.invite_user, name="invite_user"),
    path("app/administration/roles/", firm_views.roles_list, name="roles_list"),
    path("app/administration/roles/new/", firm_views.role_create, name="role_create"),
    path("app/administration/roles/<uuid:role_id>/edit/", firm_views.role_edit, name="role_edit"),
    path("app/firms/<uuid:firm_id>/", firm_views.firm_detail, name="firm_detail"),
]
