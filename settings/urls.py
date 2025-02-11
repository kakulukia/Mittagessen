from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView, TemplateView
from rest_framework import routers

from invoices.views import generate_invoice
from meals.views import (
    WeekViewSet,
    alexa_today,
    CurrentUserView,
    PlanViewSet,
    DayViewSet,
    MealViewSet,
    show_menu,
    mark_suggestion_as_seen,
    create_suggestion,
    unseen_suggestion_number
)


router = routers.DefaultRouter()
router.register("weeks", WeekViewSet)
router.register("days", DayViewSet)
router.register("plans", PlanViewSet)
router.register("meals", MealViewSet)

urlpatterns = [
    path(
        "admin/mark-suggestion-as-seen/<int:suggestion_id>/",
        mark_suggestion_as_seen,
        name="mark-suggestion-as-seen",
    ),
    path("admin/", admin.site.urls),
    path("today", alexa_today),
    path("", show_menu),
    path("kueche/", RedirectView.as_view(url="http://localhost:8080/kueche", query_string=True)),
    path("api/", include(router.urls)),
    path("api/current-user/", CurrentUserView.as_view()),
    path("api/unseen-suggestions", unseen_suggestion_number),
    path("create-suggestion/", create_suggestion),
    path("impressum", TemplateView.as_view(template_name="imprint.pug")),
    path("datenschutz", TemplateView.as_view(template_name="privacy.pug")),
    path('invoice/', generate_invoice, name='generate_invoice'),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path(r"__debug__/", include(debug_toolbar.urls)),
        path("__reload__/", include("django_browser_reload.urls")),
    ] + urlpatterns
