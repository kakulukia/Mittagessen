from datetime import date
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

import pendulum


def pendulum_instance(value: date):
    return pendulum.datetime(*value.timetuple()[:3], tz='local')


class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening

