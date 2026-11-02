from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from django.template.loader import render_to_string
from django.test import SimpleTestCase


class InvoicePdfTemplateTests(SimpleTestCase):
    def render_invoice(self, total, template):
        invoice = SimpleNamespace(
            invoice_number="2026-0081",
            date=date(2026, 11, 2),
            customer=SimpleNamespace(address="Beispielkunde\nTeststraße 1"),
            text="Bezug: Rechnung 2026-0064 vom 31.08.2026",
            total=total,
            net=Decimal("-675.00") if total and total < 0 else Decimal("675.00"),
            tax=Decimal("-47.25") if total and total < 0 else Decimal("47.25"),
            days=SimpleNamespace(all=list),
        )
        return render_to_string(template, {"invoice": invoice})

    def test_cancellation_has_reference_and_no_payment_request(self):
        for template in ("invoice.pug", "invoice_sum.pug"):
            with self.subTest(template=template):
                html = self.render_invoice(Decimal("-722.25"), template)
                self.assertRegex(html, r"<h1>\s*Stornorechnung\s*</h1>")
                self.assertIn("Stornobetrag", html)
                self.assertIn("Rechnung 2026-0064 vom 31.08.2026", html)
                self.assertIn("-722,25", html)
                self.assertIn("Leistungsdatum siehe Rechnungspositionen", html)
                self.assertNotIn("Rechnungsdatum entspricht", html)
                self.assertNotIn("Bitte überweisen", html)

    def test_regular_zero_and_incomplete_invoices_keep_existing_wording(self):
        for template in ("invoice.pug", "invoice_sum.pug"):
            for total in (Decimal("722.25"), Decimal("0.00"), None):
                with self.subTest(template=template, total=total):
                    html = self.render_invoice(total, template)
                    self.assertRegex(html, r"<h1>\s*Rechnung\s*</h1>")
                    self.assertIn("Rechnungsbetrag", html)
                    self.assertIn("Bitte überweisen", html)
                    self.assertIn("Rechnungsdatum entspricht", html)
                    self.assertNotIn("Stornorechnung", html)
