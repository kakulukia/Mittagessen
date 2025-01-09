from django.db import models
from django_undeletable.models import BaseModel


# Create your models here.
class Customer(BaseModel):
    salutation = models.CharField("Anrede", max_length=200, choices=[("Herr", "Herr"), ("Frau", "Frau")])
    company = models.CharField("Firma", max_length=200, blank=True)
    name = models.CharField(max_length=200)
    street = models.CharField("Straße", max_length=200)
    zip = models.CharField("PLZ", max_length=5)
    city = models.CharField("Stadt", max_length=200)

    email = models.EmailField("E-Mail", blank=True)

    class Meta(BaseModel.Meta):
        verbose_name = "Kunde"
        verbose_name_plural = "Kunden"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Invoice(BaseModel):
    invoice_number = models.CharField("Rechnungsnummer", max_length=200)
    date = models.DateField("Lieferdatum")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="invoices", verbose_name="Kunde")
    net = models.DecimalField("Netto", max_digits=10, decimal_places=2, null=True)
    tax = models.DecimalField("MwSt.", max_digits=10, decimal_places=2, null=True)
    total = models.DecimalField("Brutto", max_digits=10, decimal_places=2, null=True)

    class Meta(BaseModel.Meta):
        verbose_name = "Rechnung"
        verbose_name_plural = "Rechnungen"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.invoice_number} ({self.date})"
