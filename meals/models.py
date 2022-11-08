import re
from datetime import datetime, timedelta

import pendulum
from django.db import models

# Create your models here.
from django.template.defaultfilters import date
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django_undeletable.models import BaseModel

from meals.utils import pendulum_instance


class Meal(BaseModel):
    name = models.CharField(verbose_name="Name", max_length=200)

    highlight = models.BooleanField(verbose_name="Highlight", default=False)
    headline = models.BooleanField(verbose_name="Wahlessen", default=False)
    vegi = models.BooleanField(verbose_name="vegetarisch", default=False)
    vegan = models.BooleanField(verbose_name="vegan", default=False)
    side_dish = models.BooleanField(verbose_name="Beilage", default=False)

    class Meta(BaseModel.Meta):
        ordering = ["name"]
        verbose_name = "Gericht"
        verbose_name_plural = "Gerichte"

    def __str__(self):
        return self.name

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.side_dish = self.name.startswith("-")

        super().save(force_insert, force_update, using, update_fields)


class Week(BaseModel):
    start = models.DateField(verbose_name="Wochenstart", unique=True)
    headline = models.TextField(verbose_name="Überschrift", blank=True)
    footer = models.TextField(verbose_name="Fußzeile", blank=True)
    published = models.BooleanField(verbose_name="veröffentlicht", default=False)

    class Meta(BaseModel.Meta):
        ordering = ['-start']
        verbose_name = "Woche"
        verbose_name_plural = "Wochen"

    def __str__(self):
        return f"KW {self.kw} ({date(self.start)})"

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)

        if not self.days.count():
            current_date = pendulum_instance(self.start)
            for i in range(5):
                self.days.create(date=current_date.date())
                current_date = current_date.add(days=1)

    @property
    def kw(self):
        start = pendulum_instance(self.start)
        return start.week_of_year

    @property
    def end(self):
        dings = pendulum_instance(self.start).add(days=4)
        return datetime.fromisoformat(dings.to_datetime_string())

    def next_week(self):
        next_start = self.start + timedelta(days=7)
        week = Week.data.filter(start=next_start)
        if week:
            return week.get()
        return None

    def start_in_past(self):
        return now().date() >= self.start

    @property
    def safe_footer(self):
        text = re.sub('<img[^>]*>', '', self.footer)
        return mark_safe(text)

    @property
    def background(self):
        match = re.search('<img src="([^>]*)">', self.footer)

        if match:
            return match.groups()[0]
        return None


class Plan(BaseModel):
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name="plans")
    day = models.ForeignKey("Day", on_delete=models.CASCADE, related_name="plans")

    price = models.DecimalField(verbose_name="Preis", decimal_places=2, max_digits=7, blank=True)
    order = models.IntegerField(verbose_name="Sortierung", default=0)

    class Meta(BaseModel.Meta):
        ordering = ("order", "created")

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.price and not self.id:
            qs = Plan.data.filter(meal=self.meal, price__gt=0).order_by("-created")
            if qs:
                self.price = qs.first().price
            else:
                self.price = 0

        if not self.order:
            self.order = self.day.plans.count() + 1

        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return f"({self.order}) {self.meal.name}"

    def price_transcription(self):
        if self.meal.headline or not self.price:
            return ''

        # front = self.price.as_tuple().digits[:-2]
        # front = str.join("", [str(val) for val in front])
        #
        # back = self.price.as_tuple().digits[-2:]
        # back = str.join("", [str(val) for val in back])
        #
        # string = f"für {front}"
        # if not back == "00":
        #     string += f' {back}'
        # else:
        #     string += " €"

        string = f'für {self.price} €'
        return string


class Day(BaseModel):
    date = models.DateField(unique=True)
    week = models.ForeignKey(Week, on_delete=models.CASCADE, related_name="days")
    meals = models.ManyToManyField(Meal, through=Plan)
    closed = models.BooleanField(verbose_name="geschlossen", default=False)
    alt_text = models.TextField(blank=True)

    class Meta(BaseModel.Meta):
        ordering = ("date",)
        verbose_name = "Tag"
        verbose_name_plural = "Tage"

    def __str__(self):
        return date(self.date)

    def transcribe(self):
        string = render_to_string("day_transcription.txt", {"day": self})
        return string

    @property
    def safe_alt_text(self):
        text = re.sub('<img[^>]*>', '', self.alt_text)
        return mark_safe(text)

    @property
    def background(self):
        match = re.search('<img src="([^>]*)">', self.alt_text)

        if match:
            return match.groups()[0]
        return None
