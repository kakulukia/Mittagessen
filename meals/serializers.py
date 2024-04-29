import re

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
            "vegan",
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
            "published",
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
            "closed",
            "alt_text",
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
            "start",
            "days",
            "kw",
            "footer",
            "safe_footer",
            "published",
            "background",
        )

    def to_representation(self, week: Week):
        representation = super().to_representation(week)
        week_dates = f'{date(week.start, "d.")}-{date(week.end, "d.m.Y")}'
        representation["dateDisplay"] = week_dates
        representation["headline"] = week.location.headline
        representation["location_logo"] = week.location.logo.name
        match = re.search(r"<img.*?>", week.footer)
        representation["footer"] = ""
        if match:
            representation["footer"] = match.group()
        return representation

    def validate(self, attrs):
        if "published" in attrs and attrs["published"]:
            if Plan.data.filter(
                day__in=self.instance.days.all(), price=0, meal__headline=False
            ).exists():
                raise serializers.ValidationError("Bitte erst alle Preise hinterlegen!")
        return self.initial_data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username"]
