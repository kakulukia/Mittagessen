from django.contrib import admin

from meals.models import Meal, Week, Day, Plan


@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    ...


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
