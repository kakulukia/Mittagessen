from datetime import date
import pendulum


def pendulum_instance(value: date):
    return pendulum.datetime(*value.timetuple()[:3], tz='local')
