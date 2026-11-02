from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from invoices.models import Customer, Invoice, InvoiceDay


class InvoiceDeliveryMonthsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().data.create_user(username="billing-user")
        cls.customer = Customer.data.create(address="Beispielkunde\nTeststraße 1")
        cls.invoice = Invoice.data.create(
            customer=cls.customer,
            invoice_number="2026-0001",
            date=date(2026, 10, 6),
            net=Decimal("100.00"),
            tax=Decimal("7.00"),
            total=Decimal("107.00"),
        )
        for delivery_date in [date(2026, 9, 1), date(2026, 9, 30)]:
            InvoiceDay.data.create(
                customer=cls.customer, invoice=cls.invoice, date=delivery_date
            )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_list_uses_delivery_month_instead_of_invoice_date(self):
        response = self.client.get(reverse("invoice-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["date"], "2026-10-06")
        self.assertEqual(response.data[0]["delivery_months"], ["2026-09"])
        self.assertEqual(response.data[0]["total"], "107.00")

    def test_multiple_months_remain_visible_for_review(self):
        InvoiceDay.data.create(
            customer=self.customer, invoice=self.invoice, date=date(2026, 10, 1)
        )
        response = self.client.get(reverse("invoice-detail", args=[self.invoice.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["delivery_months"], ["2026-09", "2026-10"])

    def test_invoice_without_deliveries_has_no_month(self):
        self.invoice.days.all().delete()
        response = self.client.get(reverse("invoice-detail", args=[self.invoice.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["delivery_months"], [])

    def test_customer_invoice_list_includes_delivery_month(self):
        response = self.client.get(
            reverse("customer-invoices", args=[self.customer.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["delivery_months"], ["2026-09"])

    def test_list_fetches_customers_and_deliveries_in_two_queries(self):
        other_customer = Customer.data.create(address="Zweiter Kunde")
        Invoice.data.create(
            customer=other_customer, invoice_number="2026-0002", date=date(2026, 10, 6)
        )
        with self.assertNumQueries(2):
            response = self.client.get(reverse("invoice-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
