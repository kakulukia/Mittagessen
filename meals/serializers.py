from django.template.defaultfilters import date
from rest_framework import serializers

from meals.models import Week, Day, Meal, Plan
from users.models import User


class MealSerializer(serializers.ModelSerializer):

    class Meta:
        model = Meal
        fields = (
            'id',
            'name',
            'headline',
            'vegi',
            'side_dish',
        )


class PlanSerializer(serializers.ModelSerializer):
    meal = MealSerializer()

    class Meta:
        model = Plan
        fields = (
            'id',
            'meal',
            'price',
            'order',
        )


class DaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Day
        fields = (
            'id',
            'date',
        )

    def to_representation(self, day: Day):
        data = super().to_representation(day)
        data['plans'] = PlanSerializer(day.plans.all(), many=True).data
        data['dateDisplay'] = date(day.date)
        return data


class WeekSerializer(serializers.ModelSerializer):
    days = DaySerializer(many=True)

    class Meta:
        model = Week
        fields = (
            'id',
            'headline',
            'footer',
            'start',
            'days',
            'kw',
        )

    def to_representation(self, week: Week):
        representation = super().to_representation(week)
        representation['dateDisplay'] = date(week.start)
        return representation


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            'username'
        ]
