from datetime import date

import pendulum
from django.utils.html import strip_tags
from rest_framework.authentication import BasicAuthentication, SessionAuthentication


def pendulum_instance(value: date):
    return pendulum.datetime(*value.timetuple()[:3], tz="local")


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


def get_or_create_week(start, location, copy=False):
    from meals.models import Week

    week_qs = Week.data.filter(start=start, location=location)

    if week_qs:
        week = week_qs.get()
    else:
        week = Week.data.create(start=start, location=location)

        if '<img' not in week.footer:
            last_year = pendulum.parse(start.isoformat()).subtract(years=1).start_of("week")
            last_week = Week.data.filter(start=last_year.date(), footer__isnull=False).first()
            week.footer = last_week.footer if last_week else ""
            week.save()

    if copy:
        week.copy_from_other_location()

    return week
