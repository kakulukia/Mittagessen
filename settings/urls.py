from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from meals.views import WeekViewSet, index, CurrentUserView, PlanViewSet, DayViewSet, MealViewSet

router = routers.DefaultRouter()
router.register('weeks', WeekViewSet)
router.register('days', DayViewSet)
router.register('plans', PlanViewSet)
router.register('meals', MealViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),

    path('', index, {'path': ''}),

    path('api/', include(router.urls)),
    path('api/current-user/', CurrentUserView.as_view()),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [path(r"__debug__/", include(debug_toolbar.urls))] + urlpatterns
