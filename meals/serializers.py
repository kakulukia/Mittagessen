from django.template.defaultfilters import date
from rest_framework import serializers

from meals.models import Day, Meal, Plan, Week
from users.models import User


class MealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meal
        fields = (
            "id",
            "name",
            "headline",
            "vegi",
            "side_dish",
        )


class PlanSerializer(serializers.ModelSerializer):
    meal = MealSerializer(read_only=True)
    meal_id = serializers.PrimaryKeyRelatedField(queryset=Meal.data.all(), source="meal")

    class Meta:
        model = Plan
        fields = (
            "id",
            "meal",
            "meal_id",
            "day",
            "price",
            "order",
        )

    def create(self, validated_data):
        plan = Plan(**validated_data)
        plan.save()
        return plan


class DaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Day
        fields = (
            "id",
            "date",
        )

    def to_representation(self, day: Day):
        data = super().to_representation(day)
        data["plans"] = PlanSerializer(day.plans.all(), many=True).data
        data["weekday"] = date(day.date, "l")
        data["dateDisplay"] = date(day.date, "d.m.y")
        return data


class WeekSerializer(serializers.ModelSerializer):
    days = DaySerializer(many=True)

    class Meta:
        model = Week
        fields = (
            "id",
            "headline",
            "footer",
            "start",
            "days",
            "kw",
        )

    def to_representation(self, week: Week):
        representation = super().to_representation(week)
        week_dates = f'{date(week.start, "d.m.")} - {date(week.end, "d.m.Y")}'
        representation["dateDisplay"] = week_dates
        return representation


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username"]
