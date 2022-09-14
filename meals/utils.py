from datetime import date

import pendulum
from rest_framework.authentication import BasicAuthentication, SessionAuthentication


def pendulum_instance(value: date):
    return pendulum.datetime(*value.timetuple()[:3], tz="local")


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


def get_or_create_week(start):
    from meals.models import Week

    week_qs = Week.data.filter(start=start)

    if week_qs:
        week = week_qs.get()
    else:
        week = Week.data.create(start=start)
    return week
