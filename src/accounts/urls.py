from django.urls import path

from accounts import views


urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("password_reset/", views.PublicPasswordResetView.as_view(), name="password_reset"),
    path("invitations/<str:token>/accept/", views.accept_invitation, name="accept_invitation"),
    path("switch-firm/<uuid:firm_id>/", views.switch_firm, name="switch_firm"),
]
