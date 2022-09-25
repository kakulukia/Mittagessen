import datetime
import re
from random import choice

import pendulum
from django.http import JsonResponse
from django.shortcuts import render
from django.template.defaultfilters import date
from django.views.generic import DetailView
from django_weasyprint import WeasyTemplateResponseMixin
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from meals.models import Day, Meal, Plan, Week
from meals.serializers import (
    DaySerializer,
    MealSerializer,
    PlanSerializer,
    UserSerializer,
    WeekSerializer,
)
from meals.utils import get_or_create_week


class WeekViewSet(ModelViewSet):
    queryset = Week.data.all()
    serializer_class = WeekSerializer

    @action(url_path="current-week", detail=False, methods=["GET"])
    def get_current_week(self, request):
        start = pendulum.today().add(days=2).start_of("week")
        week = get_or_create_week(start.date())
        return Response(WeekSerializer(week).data)

    @action(url_path="get-week", detail=False, methods=["GET"])
    def get_week(self, request):
        if "date" not in request.GET:
            return Response(status=400)
        start = pendulum.parse(request.GET.get("date")).add(days=2).start_of("week")
        week = get_or_create_week(start.date())
        return Response(WeekSerializer(week).data)


class DayViewSet(ModelViewSet):
    queryset = Day.data.all()
    serializer_class = DaySerializer


class PlanViewSet(ModelViewSet):
    queryset = Plan.data.all()
    serializer_class = PlanSerializer


class MealViewSet(ModelViewSet):
    queryset = Meal.data.all()
    serializer_class = MealSerializer


def alexa_today(request):
    day_qs = Day.data.filter(date=datetime.date.today())
    next_day = Day.data.filter(date__gt=datetime.date.today(), closed=False).first()
    day_name = f"{date(next_day.date, 'l')}"

    closed = [
        "Heute ist leider geschlossen.",
        "Tut mir leid, aber heute musst du leider selber kochen.",
        "Die Kochteufel haben heut frei.",
    ]

    added = [
        " Wir sind DAY-NAME wieder für dich da.",
        " Wir freuen uns darauf, am DAY-NAME wieder für dich da zu sein.",
    ]

    weekend_only = [
        "Hoch die Hände, Wochenende!",
    ]

    if pendulum.today().weekday() > 4:
        closed += weekend_only

    if day_qs:
        day = day_qs.first()

        if day.closed:
            text = choice(closed) + choice(added),
        else:
            text = day.transcribe()
    else:
        text = choice(closed) + choice(added)

    text = re.sub('DAY-NAME', day_name, text)

    return JsonResponse({"text": text})


class CurrentUserView(APIView):
    def get(self, request):
        if request.user.is_authenticated:
            return Response(UserSerializer(request.user).data)
        return Response(status=status.HTTP_401_UNAUTHORIZED)


def show_menu(request):
    if "date" in request.GET:
        start = pendulum.parse(request.GET.get("date")).add(days=2).start_of("week")
    else:
        start = pendulum.today().add(days=2).start_of("week")
    week = get_or_create_week(start.date())
    return render(request, "menu.pug", {"week": week})


class PrintWeekView(WeasyTemplateResponseMixin, DetailView):
    template_name = 'print-week.pug'
    context_object_name = 'week'

    # show pdf in-line (default: True, show download dialog)
    pdf_attachment = True

    def get_object(self, **kwargs):
        if "date" in self.request.GET:
            start = pendulum.parse(self.request.GET.get("date")).add(days=2).start_of("week")
        else:
            start = pendulum.today().add(days=2).start_of("week")
        week = get_or_create_week(start.date())
        return week

    def get_pdf_filename(self):
        return f'Speiseplan {self.request.GET.get("date")}.pdf'

