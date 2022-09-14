import re
from datetime import datetime

import pendulum
from django.db import models

# Create your models here.
from django.template.defaultfilters import date
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django_undeletable.models import BaseModel

from meals.utils import pendulum_instance


class Meal(BaseModel):
    name = models.CharField(verbose_name="Name", max_length=200)

    headline = models.BooleanField(verbose_name="FETT", default=False)
    vegi = models.BooleanField(verbose_name="vegetarisch", default=False)
    side_dish = models.BooleanField(verbose_name="Beilage", default=False)

    class Meta(BaseModel.Meta):
        ordering = ["name"]
        verbose_name = "Mahlzeit"
        verbose_name_plural = "Mahlzeiten"

    def __str__(self):
        return self.name

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.side_dish = self.name.startswith("-")

        super().save(force_insert, force_update, using, update_fields)


class Week(BaseModel):
    start = models.DateField(verbose_name="Wochenstart")
    headline = models.TextField(verbose_name="Überschrift", blank=True)
    footer = models.TextField(verbose_name="Fußzeile", blank=True)
    published = models.BooleanField(verbose_name="veröffentlicht", default=False)

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


class Plan(BaseModel):
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name="plans")
    day = models.ForeignKey("Day", on_delete=models.CASCADE, related_name="plans")

    price = models.DecimalField(verbose_name="Preis", decimal_places=2, max_digits=7, blank=True)
    order = models.IntegerField(verbose_name="Sortierung", default=0)

    class Meta(BaseModel.Meta):
        ordering = ("order", "created")

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.price:
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
        front = self.price.as_tuple().digits[:-2]
        front = str.join("", [str(val) for val in front])

        back = self.price.as_tuple().digits[-2:]
        back = str.join("", [str(val) for val in back])

        string = f"für {front} €"
        if not back == "00":
            string += f' {back}'

        return string


class Day(BaseModel):
    date = models.DateField()
    week = models.ForeignKey(Week, on_delete=models.CASCADE, related_name="days")
    meals = models.ManyToManyField(Meal, through=Plan)
    closed = models.BooleanField(verbose_name="geschlossen", default=False)
    alt_text = models.TextField()

    class Meta(BaseModel.Meta):
        ordering = ("date",)

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
