from django.contrib import admin
from django.db.models import OuterRef, Subquery

from meals.models import Day, Meal, Plan, Week


@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ['name', 'created', 'latest']
    ordering = ['-created']
    search_fields = ['name']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        latest_plan_subquery = Plan.data.filter(
            meal=OuterRef('pk')).order_by('-created').values('day__date')[:1]
        qs = qs.annotate(latest=Subquery(latest_plan_subquery))
        return qs

    def latest(self, obj):
        return obj.latest
    latest.short_description = "Zuletzt"
    latest.admin_order_field = 'latest'


class DayInlineAdmin(admin.TabularInline):
    model = Day


class PlanInline(admin.TabularInline):
    model = Plan


@admin.register(Week)
class WeekAdmin(admin.ModelAdmin):
    inlines = (DayInlineAdmin,)


@admin.register(Day)
class DayAdmin(admin.ModelAdmin):
    inlines = [PlanInline]
    list_display = ['created', 'date']
    ordering = ['-date']
