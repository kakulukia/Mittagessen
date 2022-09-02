import pendulum
from django.http import JsonResponse, HttpResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from meals.models import Week, Plan, Day, Meal
from meals.serializers import WeekSerializer, UserSerializer, PlanSerializer, DaySerializer, MealSerializer


class WeekViewSet(ModelViewSet):
    queryset = Week.data.all()
    serializer_class = WeekSerializer

    @action(url_path='current-week', detail=False, methods=['GET'])
    def get_current_week(self, request):
        start = pendulum.today().start_of('week')
        week = Week.data.get(start=start.date())
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


def index(request, path=''):
    print(path)
    content = {
      "text": """
          Heute gibt es: 
              Szegediner Gulasch mit Kartoffeln für 7€. 
              Asiatische Reispfanne mit Gemüse für 6€. 
              Und Wildgulaschsuppe für 5€ 50. 
      """,
    }
    return JsonResponse(content)


class CurrentUserView(APIView):

    def get(self, request):
        if request.user.is_authenticated:
            return Response(UserSerializer(request.user).data)
        return Response(status=status.HTTP_401_UNAUTHORIZED)
