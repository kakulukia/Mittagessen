from decimal import Decimal

from django.db import models
from django.template.loader import render_to_string
from django.utils.timezone import now
from weasyprint import HTML

from invoices.utils import BaseModel, django_url_fetcher


# Create your models here.
class Customer(BaseModel):
    name = models.CharField(max_length=200, blank=True)
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

    def save(self, *args, **kwargs):
        # if the date is in the past, set delivered to true already
        if self.date < now().date():
            self.delivered = True
        super().save(*args, **kwargs)


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

    @property
    def single_net_price(self):
        # keep the price as is for takeaway + so its 7% plus for delivery
        if self.day.invoice.customer.delivery_type == "delivery":
            return self.price

        price = round(self.price / Decimal(1.07), 2)
        return price

    @property
    def net_price(self):
        return self.single_net_price * self.count


class Invoice(BaseModel):
    invoice_number = models.CharField("Rechnungsnummer", max_length=200)
    date = models.DateField("Lieferdatum")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="invoices", verbose_name="Kunde")
    net = models.DecimalField("Netto", max_digits=10, decimal_places=2, null=True)
    tax = models.DecimalField("MwSt.", max_digits=10, decimal_places=2, null=True)
    total = models.DecimalField("Brutto", max_digits=10, decimal_places=2, null=True)

    text = models.TextField("Rechnungstext", blank=True, default="")

    class Meta(BaseModel.Meta):
        verbose_name = "Rechnung"
        verbose_name_plural = "Rechnungen"
        ordering = ["-invoice_number"]

    def __str__(self):
        return f"{self.invoice_number} ({self.date} - {self.total} €)"

    @classmethod
    def create_from_open_days(cls, customer, invoice_text):
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

        # Set invoice date to the current date
        invoice_date = now().date()

        new_invoice = cls.data.create(
            invoice_number='',
            date=invoice_date,
            customer=customer,
            text=invoice_text,
        )

        invoice_count = Invoice.data.filter(date__year=invoice_date.year).count()
        if invoice_date.year == 2025:
            invoice_count += 52
        new_invoice.invoice_number = f"{invoice_date.year}-{invoice_count:04d}"
        new_invoice.save()

        month_open_days.update(invoice=new_invoice)
        new_invoice.update_prices()

        return new_invoice

    def generate_pdf(self):
        """
        Generate a PDF for this invoice using sample items.
        """
        context = {
            'invoice': self,
        }

        html_string = render_to_string('invoice.pug', context)
        html = HTML(
            string=html_string,
            url_fetcher=django_url_fetcher,
            base_url='file://',
        )
        pdf_data = html.write_pdf()
        return pdf_data

    def update_prices(self):

        # update net, tax total
        net = sum(sum(meal.net_price for meal in day.meals.all()) for day in self.days.all())
        tax = round(net * Decimal(0.07), 2)
        total = net + tax

        self.net = net
        self.tax = tax
        self.total = total
        self.save()

    @property
    def for_month(self):
        return self.days.last().date

