
from django.db import models
from django.template.loader import render_to_string
from django_undeletable.models import BaseModel
from django_weasyprint.utils import django_url_fetcher
from weasyprint import HTML


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
    invoice = models.ForeignKey("Invoice", on_delete=models.SET_NULL, related_name="days", null=True, blank=True)

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

    class Meta(BaseModel.Meta):
        verbose_name = "Rechnung"
        verbose_name_plural = "Rechnungen"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.invoice_number} ({self.date})"

    @classmethod
    def create_from_open_days(cls, customer):
        """
        Create a new invoice for the customer based on open days.
        Only includes days that are delivered and not yet invoiced,
        restricted to the month of the first open day.
        """

        open_days = customer.invoice_days.filter(delivered=True, invoice__isnull=True)
        if not open_days.exists():
            return None

        first_open_day = open_days.order_by('date').first()
        target_year = first_open_day.date.year
        target_month = first_open_day.date.month

        month_open_days = open_days.filter(date__year=target_year, date__month=target_month)

        # Set invoice date as the latest date in the month
        invoice_date = max(day.date for day in month_open_days)

        new_invoice = cls.data.create(
            invoice_number='',
            date=invoice_date,
            customer=customer,
            net=0,
            tax=0,
            total=0
        )

        new_invoice.invoice_number = f"{invoice_date.year}-{new_invoice.pk + 1000}"
        new_invoice.save()

        month_open_days.update(invoice=new_invoice)

        return new_invoice

    def generate_pdf(self):
        """
        Generate a PDF for this invoice using sample items.
        """
        items = [
            {'name': 'Mittagessen', 'quantity': 4, 'price': 8, 'total': 32},
            {'name': 'Suppen', 'quantity': 1, 'price': 5, 'total': 15},
            {'name': 'Mittagessen', 'quantity': 4, 'price': 8, 'total': 32},
            {'name': 'Suppen', 'quantity': 1, 'price': 5, 'total': 15},
            {'name': 'Suppen', 'quantity': 1, 'price': 5, 'total': 15},
            {'name': 'Suppen', 'quantity': 1, 'price': 5, 'total': 15},
            {'name': 'Mittagessen', 'quantity': 4, 'price': 8, 'total': 32},
            {'name': 'Suppen', 'quantity': 1, 'price': 5, 'total': 15},
            {'name': 'Mittagessen', 'quantity': 4, 'price': 8, 'total': 32},
            {'name': 'Suppen', 'quantity': 1, 'price': 5, 'total': 15},
            {'name': 'Mittagessen', 'quantity': 4, 'price': 8, 'total': 32},
            {'name': 'Suppen', 'quantity': 1, 'price': 5, 'total': 15},
            {'name': 'Suppen', 'quantity': 1, 'price': 5, 'total': 15},
            {'name': 'Mittagessen', 'quantity': 4, 'price': 8, 'total': 32},
        ]
        net = sum(item['total'] for item in items)
        tax = round(net * 0.07, 2)
        total = net + tax

        context = {
            'invoice_number': self.invoice_number,
            'date': self.date.strftime('%d.%m.%Y'),
            'items': items,
            'net': net,
            'tax': tax,
            'total': total,
            'recipient': {
                'name': 'Max Mustermann',
                'street': 'Musterstraße 12',
                'zip': '12345',
                'city': 'Musterstadt',
            },
        }

        html_string = render_to_string('invoice.pug', context)
        html = HTML(
            string=html_string,
            url_fetcher=django_url_fetcher,
            base_url='file://',
        )
        pdf_data = html.write_pdf()
        return pdf_data

