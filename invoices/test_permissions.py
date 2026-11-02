from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from invoices.models import Customer, Invoice, InvoiceDay, InvoiceMeal
from meals.models import Location


class BillingAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().data.create_user(username="billing-user")
        cls.customer = Customer.data.create(address="Beispielkunde")
        cls.invoice = Invoice.data.create(
            customer=cls.customer, invoice_number="2026-0001", date=date(2026, 11, 2)
        )
        cls.day = InvoiceDay.data.create(
            customer=cls.customer, invoice=cls.invoice, date=date(2026, 4, 16)
        )
        cls.meal = InvoiceMeal.data.create(day=cls.day, name="Suppe", price=10)
        cls.invoice.update_prices()

    def setUp(self):
        self.client = APIClient()

    def resources(self):
        return (
            ("customer", self.customer.pk),
            ("invoice", self.invoice.pk),
            ("invoiceday", self.day.pk),
            ("invoicemeal", self.meal.pk),
        )

    def read_urls(self):
        urls = []
        for name, pk in self.resources():
            urls.extend((reverse(f"{name}-list"), reverse(f"{name}-detail", args=[pk])))
        for name, pk in (
            ("customer-invoice-days", self.customer.pk),
            ("customer-invoices", self.customer.pk),
            ("invoice-days", self.invoice.pk),
            ("invoice-pdf", self.invoice.pk),
            ("invoiceday-meals", self.day.pk),
        ):
            urls.append(reverse(name, args=[pk]))
        urls.append(reverse("invoiceday-today"))
        return urls

    @patch("invoices.models.Invoice.generate_pdf", return_value=b"%PDF-test")
    def test_anonymous_pdf_is_denied_before_rendering(self, generate_pdf):
        response = self.client.get(reverse("invoice-pdf", args=[self.invoice.pk]))
        self.assertEqual(response.status_code, 403)
        generate_pdf.assert_not_called()

    @patch("invoices.models.Invoice.generate_pdf", return_value=b"%PDF-test")
    def test_anonymous_reads_and_metadata_are_denied(self, generate_pdf):
        for url in self.read_urls():
            for method in ("get", "head", "options"):
                with self.subTest(url=url, method=method):
                    response = getattr(self.client, method)(url)
                    self.assertEqual(response.status_code, 403)
        generate_pdf.assert_not_called()

    def test_anonymous_writes_and_invoice_generation_are_denied(self):
        for name, pk in self.resources():
            requests = [("post", reverse(f"{name}-list"))]
            requests.extend(
                (method, reverse(f"{name}-detail", args=[pk]))
                for method in ("put", "patch", "delete")
            )
            for method, url in requests:
                with self.subTest(url=url, method=method):
                    response = getattr(self.client, method)(url, {}, format="json")
                    self.assertEqual(response.status_code, 403)
        response = self.client.post(
            reverse("customer-generate-invoice", args=[self.customer.pk]),
            {"invoiceText": "Unberechtigte Rechnung"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        for model in (Customer, Invoice, InvoiceDay, InvoiceMeal):
            self.assertEqual(model.data.count(), 1)

    @patch("invoices.models.Invoice.generate_pdf", return_value=b"%PDF-test")
    def test_session_login_allows_reads_pdf_and_editing(self, generate_pdf):
        self.client.force_login(self.user)
        for url in self.read_urls():
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
        generate_pdf.assert_called_once()
        response = self.client.patch(
            reverse("customer-detail", args=[self.customer.pk]),
            {"address": "Geänderter Beispielkunde"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.address, "Geänderter Beispielkunde")
        self.client.logout()
        self.assertEqual(
            self.client.get(reverse("invoice-pdf", args=[self.invoice.pk])).status_code,
            403,
        )

    def test_inactive_session_cannot_read_billing_data(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("invoice-list")).status_code, 403)

    def test_public_menu_remains_available_without_login(self):
        Location.data.get_or_create(id=1, defaults={"name": "Emmas Imbiss"})
        self.assertEqual(self.client.get("/").status_code, 200)
