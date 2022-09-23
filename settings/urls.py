from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.static import serve
from rest_framework import routers

from meals.views import WeekViewSet, alexa_today, CurrentUserView, PlanViewSet, DayViewSet, MealViewSet, show_menu, PrintWeekView

router = routers.DefaultRouter()
router.register('weeks', WeekViewSet)
router.register('days', DayViewSet)
router.register('plans', PlanViewSet)
router.register('meals', MealViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),


    path('today', alexa_today),
    path('', show_menu),
    path('print', PrintWeekView.as_view()),

    path('api/', include(router.urls)),
    path('api/current-user/', CurrentUserView.as_view()),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
      path(r"__debug__/", include(debug_toolbar.urls)),
      path("__reload__/", include("django_browser_reload.urls")),
    ] + urlpatterns
