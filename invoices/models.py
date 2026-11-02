from decimal import Decimal
from typing import ClassVar

from django.db import models, transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.timezone import now
from weasyprint import HTML

from invoices.utils import BaseModel, django_url_fetcher
from invoices.validators import normalize_whatsapp_number


# Create your models here.
class Customer(BaseModel):
    name = models.CharField(max_length=200, blank=True)
    address = models.TextField("Adresse")

    email = models.EmailField("E-Mail", blank=True)
    whatsapp_phone = models.CharField(
        "WhatsApp-Telefonnummer", max_length=32, blank=True, default="",
        db_index=True, validators=[normalize_whatsapp_number],
        help_text="Mit Ländervorwahl, zum Beispiel +49 151 23456789.",
    )
    delivery_type = models.CharField(
        "Lieferart", max_length=200, blank=True,
        choices=[("takeaway", "Abholung"), ("delivery", "Lieferung")])

    bank_account = models.CharField(
        "Zahlungsart", max_length=200, blank=False,
        choices=[("bank", "Sparkasse"), ("sumup", "SumUp")], default="bank")

    class Meta(BaseModel.Meta):
        verbose_name = "Kunde"
        verbose_name_plural = "Kunden"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # name will be the first line of address
        self.name = self.address.split("\n")[0]
        self.whatsapp_phone = normalize_whatsapp_number(self.whatsapp_phone)
        super().save(*args, **kwargs)


class InvoiceDay(BaseModel):
    date = models.DateField("Datum")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="invoice_days", verbose_name="Kunde")
    combining_dates = models.BooleanField("Kombinierte Rechnungen", default=False)
    delivered = models.BooleanField("Geliefert", default=False)
    reviewed = models.BooleanField("Bestellung geprüft", default=False)
    source_message = models.TextField("Originalnachricht", blank=True, default="")
    invoice = models.ForeignKey("Invoice", on_delete=models.SET_NULL, related_name="days", null=True, blank=True)

    class Meta:
        verbose_name = "Rechnungstag"
        verbose_name_plural = "Rechnungstage"
        ordering = ["date"]

    def __str__(self):
        return f"{self.date}"

    def save(self, *args, **kwargs):
        if self.pk:
            original = InvoiceDay.data.get(pk=self.pk)
            if any(
                getattr(original, field) != getattr(self, field)
                for field in ("date", "customer_id", "combining_dates", "source_message")
            ):
                self.reviewed = False
                if kwargs.get("update_fields") is not None:
                    kwargs["update_fields"] = set(kwargs["update_fields"]) | {"reviewed"}
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
    price_needs_review = models.BooleanField("Preis prüfen", default=False)

    class Meta:
        verbose_name = "Rechnungposition"
        verbose_name_plural = "Rechnungspositionen"
        ordering = ["created"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        original = InvoiceMeal.data.filter(pk=self.pk).first() if self.pk else None
        if original and original.price != self.price:
            self.price_needs_review = False
            if kwargs.get("update_fields") is not None:
                kwargs["update_fields"] = set(kwargs["update_fields"]) | {"price_needs_review"}
        changed = original is None or any(
            getattr(original, field) != getattr(self, field)
            for field in ("day_id", "name", "price", "count", "comment", "price_needs_review")
        )
        with transaction.atomic():
            super().save(*args, **kwargs)
            if changed:
                day_ids = {self.day_id}
                if original:
                    day_ids.add(original.day_id)
                InvoiceDay.data.filter(pk__in=day_ids).update(reviewed=False)

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


@receiver(post_delete, sender=InvoiceMeal)
def invalidate_deleted_meal_review(sender, instance, **kwargs):
    InvoiceDay.data.filter(pk=instance.day_id).update(reviewed=False)


class WhatsAppMessage(BaseModel):
    sender = models.CharField("Absendername", max_length=200)
    sender_phone = models.CharField(
        "Absendernummer", max_length=32, blank=True, default="",
        validators=[normalize_whatsapp_number],
        help_text="Mit Ländervorwahl, zum Beispiel +49 151 23456789.",
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Kunde",
        help_text="Bei eindeutiger Absendernummer automatisch zugeordnet. "
        "Sonst den passenden Kunden manuell auswählen.",
    )
    received_at = models.DateTimeField("Empfangen am", default=now)
    text = models.TextField("Nachrichtentext")
    processed_at = models.DateTimeField("Bestellungen angelegt am", null=True, blank=True, editable=False)
    processing_error = models.TextField("Verarbeitungshinweis", blank=True, default="", editable=False)

    class Meta(BaseModel.Meta):
        verbose_name = "WhatsApp-Nachricht"
        verbose_name_plural = "WhatsApp-Nachrichten"
        ordering: ClassVar = ["-received_at", "-pk"]

    def __str__(self):
        return f"{self.sender}: {self.text[:80]}"

    @transaction.atomic
    def save(self, *args, **kwargs):
        self.sender_phone = normalize_whatsapp_number(self.sender_phone)
        original = WhatsAppMessage.data.select_for_update().filter(pk=self.pk).first() if self.pk else None
        if original and original.processed_at:
            self.processed_at = original.processed_at
            self.processing_error = original.processing_error
        manual_customer = self.customer_id and (
            original is None or self.customer_id != original.customer_id
        )
        number_changed = original is not None and self.sender_phone != original.sender_phone
        if not manual_customer and (not self.customer_id or number_changed):
            matches = list(Customer.data.filter(whatsapp_phone=self.sender_phone)[:2]) if self.sender_phone else []
            self.customer = matches[0] if len(matches) == 1 else None
            if kwargs.get("update_fields") is not None:
                kwargs["update_fields"] = set(kwargs["update_fields"]) | {"customer"}
        super().save(*args, **kwargs)
        if not self.processed_at:
            from invoices.intake import process_message

            process_message(self)


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

        template_name = "invoice.pug"
        if self.customer.bank_account == "sumup":
            template_name = "invoice_sum.pug"

        html_string = render_to_string(template_name, context)
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
