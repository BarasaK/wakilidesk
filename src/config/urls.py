from django.contrib import admin
from django.urls import include, path

from common.views import health
from firms import views as firm_views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", firm_views.dashboard, name="dashboard"),
    path("app/firms/<uuid:firm_id>/", firm_views.firm_detail, name="firm_detail"),
]
