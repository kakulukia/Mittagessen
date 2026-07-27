import re

from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import OuterRef, Subquery, Count
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.safestring import mark_safe

from meals.models import (
    Day,
    Location,
    LocationHeadlineRevision,
    Meal,
    Plan,
    Suggestion,
    Week,
)


# @admin.register(Stats)
# class StatsAdmin(admin.ModelAdmin):
#     list_display = ["date", "page_counter", "alexa_counter"]
#     ordering = ["-date"]


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ["name", "headline_text", "logo"]
    object_history_template = "admin/meals/location/object_history.html"
    ordering = ["name"]
    search_fields = ["name"]

    def save_model(self, request, obj, form, change):
        headline_changed = "headline" in form.changed_data
        super().save_model(request, obj, form, change)
        if headline_changed:
            LocationHeadlineRevision.objects.create(
                location=obj, headline=obj.headline, created_by=request.user
            )

    @admin.display(description="Überschrift")
    def headline_text(self, obj):
        # headline is html, so we need to strip any tags
        return re.sub(r"<[^>]*>", "", obj.headline)

    def history_view(self, request, object_id, extra_context=None):
        location = self.get_object(request, object_id)
        if location is None:
            return super().history_view(request, object_id, extra_context)

        if request.method == "POST":
            if not self.has_change_permission(request, location):
                raise PermissionDenied

            revision_ids = request.POST.getlist("headline_revision")
            if len(revision_ids) != 1:
                self.message_user(
                    request, "Bitte genau eine Version auswählen.", messages.ERROR
                )
                return HttpResponseRedirect(request.path)

            revision = get_object_or_404(
                LocationHeadlineRevision, pk=revision_ids[0], location=location
            )
            with transaction.atomic():
                location = Location.data.select_for_update().get(pk=location.pk)
                if location.headline == revision.headline:
                    self.message_user(
                        request, "Diese Version ist bereits aktiv.", messages.INFO
                    )
                    return HttpResponseRedirect(request.path)

                location.headline = revision.headline
                location.save(update_fields=["headline", "modified"])
                LocationHeadlineRevision.objects.create(
                    location=location,
                    headline=location.headline,
                    created_by=request.user,
                )
                self.log_change(
                    request,
                    location,
                    f"Überschrift aus Version #{revision.pk} wiederhergestellt.",
                )

            self.message_user(
                request, "Überschrift wurde wiederhergestellt.", messages.SUCCESS
            )
            return HttpResponseRedirect(request.path)

        revisions = location.headline_revisions.select_related("created_by")
        return super().history_view(
            request,
            object_id,
            {
                **(extra_context or {}),
                "headline_revisions": revisions,
                "can_restore_headline": self.has_change_permission(
                    request, location
                )
                and revisions.exclude(headline=location.headline).exists(),
            },
        )


@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "created",
        "latest",
        "num_plans"
    ]
    list_filter = ["vegi"]
    ordering = ["-created"]
    search_fields = ["name"]
    # actions = None

    @admin.display(description="Anzahl", ordering="num_plans")
    def num_plans(self, obj):
        return obj.num_plans

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        latest_plan_subquery = (
            Plan.data.filter(meal=OuterRef("pk")).order_by("-created").values("day__date")[:1]
        )
        qs = qs.annotate(latest=Subquery(latest_plan_subquery))
        qs = qs.annotate(
            num_plans=Subquery(
                Plan.data.filter(meal=OuterRef("pk")).values("meal").annotate(count=Count("meal")).values("count")[:1]
            )
        )
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
