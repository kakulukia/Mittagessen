import re
from datetime import datetime, timedelta
from functools import cached_property

from ckeditor.fields import RichTextField
from django.db import models
from django.db.models import UniqueConstraint

# Create your models here.
from django.template.defaultfilters import date
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django_undeletable.models import BaseModel

from meals.utils import pendulum_instance


class Stats(BaseModel):
    date = models.DateField(unique=True)
    page_counter = models.IntegerField(default=0)
    alexa_counter = models.IntegerField(default=0)


class Location(BaseModel):
    name = models.CharField(verbose_name="Name", max_length=50)
    headline = RichTextField(verbose_name="Überschrift", blank=True)
    logo = models.ImageField(verbose_name="Logo", upload_to="logos", blank=True)

    def __str__(self):
        return self.name


class Meal(BaseModel):
    name = models.CharField(verbose_name="Name", max_length=200)

    highlight = models.BooleanField(verbose_name="Highlight", default=False)
    headline = models.BooleanField(verbose_name="Wahlessen", default=False, help_text="Fett geschrieben, "
                                                                                      "ohne Preisanzeige")
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
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="weeks")
    start = models.DateField(verbose_name="Wochenstart", blank=True)
    headline = models.TextField(verbose_name="Überschrift", blank=True)
    footer = models.TextField(verbose_name="Fußzeile", blank=True)
    published = models.BooleanField(verbose_name="veröffentlicht", default=False)
    special_menu = models.ForeignKey(
        to="meals.Plan", on_delete=models.SET_NULL,
        verbose_name="Gericht der Woche", null=True, blank=True,
        editable=False,
    )

    class Meta(BaseModel.Meta):
        ordering = ["-start"]
        verbose_name = "Woche"
        verbose_name_plural = "Wochen"
        constraints = [
            UniqueConstraint(fields=["location", "start"], name="unique_week")
        ]

    def __str__(self):
        return f"KW {self.kw} ({date(self.start)})"

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)

        if not self.days.count():
            current_date = pendulum_instance(self.start)
            for i in range(5):
                self.days.create(date=current_date.date())
                current_date = current_date.add(days=1)

    @cached_property
    def is_closed(self):
        return not self.days.filter(closed=False).exists()

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
        text = re.sub("<img[^>]*>", "", self.footer)
        return mark_safe(text)

    @property
    def background(self):
        match = re.search('<img src="([^>]*)">', self.footer)

        if match:
            return match.groups()[0]
        return None

    def copy_from_other_location(self):

        if Plan.data.filter(day__week=self).count() > 0:
            return

        other_location_id = 2 if self.location_id == 1 else 1

        qs = Week.data.filter(start=self.start, location=other_location_id)
        if not qs.exists():
            return
        other_week = qs.get()

        for other_day in other_week.days.all():
            this_day = self.days.get(date=other_day.date)
            for plan in other_day.plans.all():
                new_plan = plan
                new_plan.pk = None
                new_plan.day = this_day

                # update price if possible
                qs = Plan.data.filter(meal=plan.meal, day__week__location=self.location)
                if qs.exists():
                    new_plan.price = qs.order_by('-created').first().price
                # else:
                #     # automatic price adjustment for the other location
                #     new_plan.price = new_plan.price + 3 if self.location.id == 2 else new_plan.price - 3
                #     # round(4.25 * 1.2 * 2) / 2 << runden auf 0.5er Schritte

                new_plan.save()

            if other_day.alt_text and other_day.closed:
                this_day.closed = True
                this_day.alt_text = other_day.alt_text
                this_day.save()

        self.footer = other_week.footer
        self.save()


class Plan(BaseModel):
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name="plans")
    day = models.ForeignKey("Day", on_delete=models.CASCADE, related_name="plans", null=True, blank=True)

    price = models.DecimalField(verbose_name="Preis", decimal_places=2, max_digits=7, blank=True)
    order = models.IntegerField(verbose_name="Sortierung", default=0)

    class Meta(BaseModel.Meta):
        ordering = ("order", "created")

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.price and not self.id:
            search_location = 2
            if self.day:
                search_location = self.day.week.location_id
            qs = Plan.data.filter(
                meal=self.meal,
                price__gt=0,
                day__week__location=search_location
            ).order_by("-modified")
            if qs:
                self.price = qs.first().price
            else:
                self.price = 0

        if not self.order and self.day:
            self.order = self.day.plans.count() + 1

        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return f"({self.order}) {self.meal.name}"

    def price_transcription(self):
        if self.meal.headline or not self.price:
            return ""

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

        string = f"für {self.price} €".replace('.', ',')
        return string


class Day(BaseModel):
    date = models.DateField()
    week = models.ForeignKey(Week, on_delete=models.CASCADE, related_name="days")
    meals = models.ManyToManyField(Meal, through=Plan)
    closed = models.BooleanField(verbose_name="geschlossen", default=False)
    alt_text = models.TextField(blank=True)

    class Meta(BaseModel.Meta):
        ordering = ("date",)
        verbose_name = "Tag"
        verbose_name_plural = "Tage"
        constraints = [
            UniqueConstraint(fields=["date", "week"], name="unique_day")
        ]

    def __str__(self):
        return date(self.date)

    def transcribe(self):
        string = render_to_string("day_transcription.txt", {"day": self})
        return string

    @property
    def safe_alt_text(self):
        text = re.sub("<img[^>]*>", "", self.alt_text)
        return mark_safe(text)

    @property
    def background(self):
        match = re.search('<img src="([^>]*)">', self.alt_text)

        if match:
            return match.groups()[0]
        return None


class Suggestion(BaseModel):
    name = models.CharField(max_length=200)
    seen = models.BooleanField(default=False, verbose_name="gesehen")

    class Meta(BaseModel.Meta):
        verbose_name = "Vorschlag"
        verbose_name_plural = "Vorschläge"
        ordering = ['seen', 'created']
