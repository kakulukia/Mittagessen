import re

from django.contrib import admin
from django.db.models import OuterRef, Subquery
from django.urls import reverse
from django.utils.safestring import mark_safe

from meals.models import Day, Meal, Plan, Week, Suggestion, Location


# @admin.register(Stats)
# class StatsAdmin(admin.ModelAdmin):
#     list_display = ["date", "page_counter", "alexa_counter"]
#     ordering = ["-date"]


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ["name", "headline_text", "logo"]
    ordering = ["name"]
    search_fields = ["name"]

    @admin.display(description="Überschrift")
    def headline_text(self, obj):
        # headline is html, so we need to strip any tags
        return re.sub(r"<[^>]*>", "", obj.headline)


@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ["name", "created", "latest"]
    list_filter = ["vegi"]
    ordering = ["-created"]
    search_fields = ["name"]
    actions = None

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        latest_plan_subquery = (
            Plan.data.filter(meal=OuterRef("pk")).order_by("-created").values("day__date")[:1]
        )
        qs = qs.annotate(latest=Subquery(latest_plan_subquery))
        return qs

    def latest(self, obj):
        return obj.latest

    latest.short_description = "Zuletzt"
    latest.admin_order_field = "latest"


class DayInlineAdmin(admin.TabularInline):
    model = Day


class PlanInline(admin.TabularInline):
    model = Plan


@admin.register(Week)
class WeekAdmin(admin.ModelAdmin):
    inlines = (DayInlineAdmin,)
    list_display = ["created", "start", "location"]


@admin.register(Day)
class DayAdmin(admin.ModelAdmin):
    inlines = [PlanInline]
    list_display = ["created", "date"]
    ordering = ["-date"]


@admin.register(Suggestion)
class SuggestionAdmin(admin.ModelAdmin):
    list_display = ["created", "name", "seen", "seen_button"]
    actions = None
    list_filter = ["seen"]

    @admin.display(description="gesehen")
    def seen_button(self, suggestion: Suggestion):
        url = reverse("mark-suggestion-as-seen", args=[suggestion.id])
        link = f"<a href='{url}'>gesehen<a/a>"
        return mark_safe(link)
