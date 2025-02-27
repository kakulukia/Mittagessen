from django.db import models
from django_undeletable.models import BaseModel


# Create your models here.
class Customer(BaseModel):
    # salutation = models.CharField("Anrede", max_length=200, choices=[("Herr", "Herr"), ("Frau", "Frau")])
    # company = models.CharField("Firma", max_length=200, blank=True)
    name = models.CharField(max_length=200, blank=True)
    # street = models.CharField("Straße", max_length=200)
    # zip = models.CharField("PLZ", max_length=5)
    # city = models.CharField("Stadt", max_length=200)
    address = models.TextField("Adresse")

    email = models.EmailField("E-Mail", blank=True)
    delivery_type = models.CharField(
        "Lieferart", max_length=200, blank=True,
        choices=[("takeaway", "Abholung"), ("delivery", "Lieferung")])

    class Meta(BaseModel.Meta):
        verbose_name = "Kunde"
        verbose_name_plural = "Kunden"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # name will be the first line of address
        self.name = self.address.split("\n")[0]
        super().save(*args, **kwargs)


class InvoiceDay(BaseModel):
    date = models.DateField("Datum")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="invoice_days", verbose_name="Kunde")
    combining_dates = models.BooleanField("Kombinierte Rechnungen", default=False)
    delivered = models.BooleanField("Geliefert", default=False)

    class Meta:
        verbose_name = "Rechnungstag"
        verbose_name_plural = "Rechnungstage"
        ordering = ["date"]

    def __str__(self):
        return f"{self.date}"


class InvoiceMeal(BaseModel):
    day = models.ForeignKey("InvoiceDay", on_delete=models.CASCADE, related_name="meals", verbose_name="Rechnungstag")

    name = models.CharField("Name", max_length=200)
    price = models.DecimalField("Preis", max_digits=10, decimal_places=2)
    count = models.IntegerField(default=1)
    delivered = models.BooleanField("Geliefert", default=False)
    comment = models.TextField("Kommentar", blank=True)

    class Meta:
        verbose_name = "Rechnungposition"
        verbose_name_plural = "Rechnungspositionen"
        ordering = ["created"]

    def __str__(self):
        return self.name


class Invoice(BaseModel):
    invoice_number = models.CharField("Rechnungsnummer", max_length=200)
    date = models.DateField("Lieferdatum")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="invoices", verbose_name="Kunde")
    net = models.DecimalField("Netto", max_digits=10, decimal_places=2, null=True)
    tax = models.DecimalField("MwSt.", max_digits=10, decimal_places=2, null=True)
    total = models.DecimalField("Brutto", max_digits=10, decimal_places=2, null=True)
    days = models.ManyToManyField("InvoiceDay", related_name="invoices", verbose_name="Rechnungstage")

    class Meta(BaseModel.Meta):
        verbose_name = "Rechnung"
        verbose_name_plural = "Rechnungen"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.invoice_number} ({self.date})"


