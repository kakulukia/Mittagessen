import pendulum
from django.db import models

# Create your models here.
from django.template.defaultfilters import date
from django_undeletable.models import BaseModel


class Meal(BaseModel):
    name = models.CharField(verbose_name='Name', max_length=200)

    headline = models.BooleanField(verbose_name='FETT', default=False)
    vegi = models.BooleanField(verbose_name='vegetarisch', default=False)
    side_dish = models.BooleanField(verbose_name='Beilage', default=False)
    price = models.DecimalField(verbose_name='Preis', decimal_places=2, max_digits=7)

    class Meta(BaseModel.Meta):
        verbose_name = 'Mahlzeit'
        verbose_name_plural = 'Mahlzeiten'

    def __str__(self):
        return self.name


class Week(BaseModel):
    start = models.DateField(verbose_name='Wochenstart')
    headline = models.TextField(verbose_name='Überschrift', blank=True)
    footer = models.TextField(verbose_name='Fußzeile', blank=True)

    def __str__(self):
        return f'KW {self.kw} ({date(self.start)})'

    def kw(self):
        start = pendulum.datetime(*self.start.timetuple()[:3], tz='local')
        return start.week_of_year


class Plan(BaseModel):
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name="plans")
    day = models.ForeignKey("Day", on_delete=models.CASCADE, related_name="plans")

    price = models.DecimalField(verbose_name='Preis', decimal_places=2, max_digits=7)
    order = models.IntegerField(verbose_name="Sortierung", default=0)

    class Meta(BaseModel.Meta):
        ordering = ('order',)


class Day(BaseModel):
    date = models.DateField()
    week = models.ForeignKey(Week, on_delete=models.CASCADE, related_name="days")
    meals = models.ManyToManyField(Meal, through=Plan)

    class Meta(BaseModel.Meta):
        ordering = ('date',)

    def __str__(self):
        return date(self.date)
