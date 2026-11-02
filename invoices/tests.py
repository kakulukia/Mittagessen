from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch
from zoneinfo import ZoneInfo

import requests
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.forms import modelform_factory
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import localdate
from rest_framework.test import APIClient

from invoices.intake import IntakeError, extract_orders, resolve_menu_order
from invoices.models import Customer, Invoice, InvoiceDay, InvoiceMeal, WhatsAppMessage
from meals.models import Location, Meal, Plan, Week


class InvoiceDeliveryMonthsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
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

    def test_list_uses_delivery_month_instead_of_invoice_date(self):
        response = APIClient().get(reverse("invoice-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["date"], "2026-10-06")
        self.assertEqual(response.data[0]["delivery_months"], ["2026-09"])
        self.assertEqual(response.data[0]["total"], "107.00")

    def test_multiple_months_remain_visible_for_review(self):
        InvoiceDay.data.create(
            customer=self.customer, invoice=self.invoice, date=date(2026, 10, 1)
        )
        response = APIClient().get(reverse("invoice-detail", args=[self.invoice.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["delivery_months"], ["2026-09", "2026-10"])

    def test_invoice_without_deliveries_has_no_month(self):
        self.invoice.days.all().delete()
        response = APIClient().get(reverse("invoice-detail", args=[self.invoice.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["delivery_months"], [])

    def test_customer_invoice_list_includes_delivery_month(self):
        response = APIClient().get(
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
            response = APIClient().get(reverse("invoice-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)


class OrderReviewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = Customer.data.create(address="Beispielkunde")
        self.day = InvoiceDay.data.create(customer=self.customer, date=localdate())
        self.meal = InvoiceMeal.data.create(
            day=self.day, name="Soljanka", count=2, price=Decimal("5.50")
        )
        self.day_url = reverse("invoiceday-detail", args=[self.day.pk])
        self.meal_url = reverse("invoicemeal-detail", args=[self.meal.pk])

    def approve(self):
        response = self.client.patch(self.day_url, {"reviewed": True}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data["reviewed"])

    def test_delivery_overview_shows_review_status_and_supports_revoking_it(self):
        url = reverse("invoiceday-deliveries")
        self.assertFalse(self.client.get(url).data[0]["reviewed"])
        self.approve()
        self.assertTrue(self.client.get(url).data[0]["reviewed"])
        self.client.patch(self.day_url, {"reviewed": False}, format="json")
        self.assertFalse(self.client.get(url).data[0]["reviewed"])

    def test_delivery_overview_and_badge_include_pending_days_at_any_date(self):
        tomorrow = InvoiceDay.data.create(customer=self.customer, date=localdate() + timedelta(days=1))
        InvoiceMeal.data.create(day=tomorrow, name="Suppe", count=1, price=5)
        InvoiceMeal.data.create(day=tomorrow, name="Salat", count=1, price=5)
        past = InvoiceDay.data.create(customer=self.customer, date=localdate() - timedelta(days=1))
        InvoiceMeal.data.create(day=past, name="Suppe", count=1, price=5)
        InvoiceDay.data.create(customer=self.customer, date=localdate())
        count_url = reverse("invoiceday-pending-count")
        deliveries_url = reverse("invoiceday-deliveries")
        self.assertEqual(self.client.get(count_url).data, {"count": 3})
        with self.assertNumQueries(2):
            response = self.client.get(deliveries_url)
        self.assertCountEqual([day["id"] for day in response.data], [self.day.pk, tomorrow.pk, past.pk])
        self.client.patch(reverse("invoiceday-detail", args=[tomorrow.pk]), {"reviewed": True}, format="json")
        self.assertEqual(self.client.get(count_url).data, {"count": 2})
        self.assertNotIn(tomorrow.pk, [day["id"] for day in self.client.get(deliveries_url).data])
        self.approve()
        self.assertIn(self.day.pk, [day["id"] for day in self.client.get(deliveries_url).data])

    def test_invoiced_days_are_excluded_from_pending_count_and_delivery_overview(self):
        invoice = Invoice.data.create(customer=self.customer, invoice_number="2026-9999", date=localdate())
        InvoiceDay.data.filter(pk=self.day.pk).update(invoice=invoice)
        self.assertEqual(self.client.get(reverse("invoiceday-pending-count")).data, {"count": 0})
        self.assertEqual(self.client.get(reverse("invoiceday-deliveries")).data, [])

    def test_order_approval_acknowledges_price_review_hints(self):
        InvoiceMeal.data.filter(pk=self.meal.pk).update(price_needs_review=True)
        self.approve()
        self.meal.refresh_from_db()
        self.assertFalse(self.meal.price_needs_review)
        response = self.client.get(self.day_url)
        self.assertFalse(response.data["meals"][0]["price_needs_review"])

    def test_price_correction_clears_hint_and_revokes_order_approval(self):
        self.approve()
        InvoiceMeal.data.filter(pk=self.meal.pk).update(price_needs_review=True)
        response = self.client.patch(self.meal_url, {"price": "6.00"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["price_needs_review"])
        self.day.refresh_from_db()
        self.assertFalse(self.day.reviewed)

    def test_changes_to_each_order_field_invalidate_review(self):
        for field, value in (
            ("name", "Schnitzel"),
            ("count", 3),
            ("price", "6.00"),
            ("comment", "Ohne Kartoffeln"),
        ):
            with self.subTest(field=field):
                self.approve()
                response = self.client.patch(self.meal_url, {field: value}, format="json")
                self.assertEqual(response.status_code, 200, response.data)
                self.day.refresh_from_db()
                self.assertFalse(self.day.reviewed)

    def test_noop_and_delivery_updates_preserve_review(self):
        self.approve()
        self.client.patch(
            self.meal_url,
            {"name": "Soljanka", "count": 2, "price": "5.50", "delivered": True},
            format="json",
        )
        response = self.client.patch(self.day_url, {"delivered": True}, format="json")
        self.assertTrue(response.data["reviewed"])
        self.assertTrue(response.data["delivered"])

    def test_adding_and_deleting_positions_invalidates_review(self):
        self.approve()
        extra = InvoiceMeal.data.create(day=self.day, name="Nachtisch", price=2)
        self.day.refresh_from_db()
        self.assertFalse(self.day.reviewed)
        self.approve()
        InvoiceMeal.data.filter(pk=extra.pk).delete()
        self.day.refresh_from_db()
        self.assertFalse(self.day.reviewed)

    def test_moving_position_invalidates_both_days(self):
        other = InvoiceDay.data.create(customer=self.customer, date=localdate())
        InvoiceDay.data.filter(pk=other.pk).update(reviewed=True)
        self.approve()
        response = self.client.patch(self.meal_url, {"day": other.pk}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertFalse(InvoiceDay.data.filter(pk__in=[other.pk, self.day.pk], reviewed=True).exists())

    def test_source_text_is_copied_per_day_and_changes_invalidate_review(self):
        text = "  Heute 2x Soljanka.\nMorgen 1x Schnitzel.\n"
        self.approve()
        response = self.client.patch(
            self.day_url, {"source_message": text, "reviewed": True}, format="json"
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["source_message"], text)
        self.assertFalse(response.data["reviewed"])
        other = InvoiceDay.data.create(
            customer=self.customer, date=date(2026, 10, 9), source_message=text
        )
        self.assertEqual(other.source_message, text)
        self.assertFalse(other.reviewed)

    def test_date_customer_and_month_changes_invalidate_review(self):
        other_customer = Customer.data.create(address="Anderer Kunde")
        for field, value in (
            ("date", "2026-10-10"),
            ("customer", other_customer.pk),
            ("combining_dates", True),
        ):
            with self.subTest(field=field):
                self.approve()
                response = self.client.patch(self.day_url, {field: value}, format="json")
                self.assertEqual(response.status_code, 200, response.data)
                self.assertFalse(response.data["reviewed"])

    def test_empty_or_invalid_orders_cannot_be_approved(self):
        self.meal.delete()
        response = self.client.patch(self.day_url, {"reviewed": True}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("reviewed", response.data)
        InvoiceMeal.data.create(day=self.day, name="", count=-1, price=-5)
        response = self.client.patch(self.day_url, {"reviewed": True}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_invalid_position_input_returns_validation_errors(self):
        self.approve()
        for payload in ({"name": ""}, {"count": -1}, {"count": "zwei"}, {"price": -1}):
            with self.subTest(payload=payload):
                response = self.client.patch(self.meal_url, payload, format="json")
                self.assertEqual(response.status_code, 400, response.data)
        self.day.refresh_from_db()
        self.assertTrue(self.day.reviewed)

    def test_unassigned_whatsapp_message_does_not_create_orders(self):
        message = WhatsAppMessage.data.create(sender="Beispielkunde", text="2x Soljanka")
        self.assertIn(WhatsAppMessage, admin.site._registry)
        self.assertEqual(InvoiceDay.data.count(), 1)
        self.assertEqual(InvoiceMeal.data.count(), 1)
        self.assertEqual(message.text, "2x Soljanka")

    def test_inbox_requires_admin_model_permission(self):
        url = reverse("admin:invoices_whatsappmessage_changelist")
        self.assertEqual(self.client.get(url).status_code, 302)
        staff = get_user_model().data.create_user(username="staff", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(url).status_code, 403)


class WhatsAppCustomerMatchingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        model = patch("invoices.intake.extract_orders", side_effect=IntakeError("Test: KI nicht erreichbar"))
        model.start()
        self.addCleanup(model.stop)
        self.customer = Customer.data.create(
            address="Beispielkunde", whatsapp_phone="+49 (151) 2345-6789"
        )

    def test_formatted_numbers_match_even_when_model_is_unavailable(self):
        self.assertEqual(self.customer.whatsapp_phone, "+4915123456789")
        message = WhatsAppMessage.data.create(
            sender="Beliebiger Anzeigename", sender_phone="0049 151 23456789", text="2x Soljanka"
        )
        self.assertEqual(message.sender_phone, "+4915123456789")
        self.assertEqual(message.customer, self.customer)
        self.assertFalse(InvoiceDay.data.exists())
        self.assertFalse(InvoiceMeal.data.exists())

    def test_empty_unknown_and_ambiguous_numbers_remain_unassigned(self):
        for phone in ("", "+4915123456788"):
            with self.subTest(phone=phone):
                message = WhatsAppMessage.data.create(
                    sender="Beispielkunde", sender_phone=phone, text="2x Soljanka"
                )
                self.assertIsNone(message.customer)
        Customer.data.create(address="Zweiter Kunde", whatsapp_phone="0049 151 23456789")
        message = WhatsAppMessage.data.create(
            sender="Beispielkunde", sender_phone=self.customer.whatsapp_phone, text="2x Soljanka"
        )
        self.assertIsNone(message.customer)
        message.customer = self.customer
        message.save()
        message.refresh_from_db()
        self.assertEqual(message.customer, self.customer)

    def test_sender_change_reassigns_or_clears_old_customer(self):
        message = WhatsAppMessage.data.create(
            sender="Kunde", sender_phone=self.customer.whatsapp_phone, text="Bestellung"
        )
        other = Customer.data.create(address="Anderer Kunde", whatsapp_phone="+4915123456788")
        message.sender_phone = other.whatsapp_phone
        message.save()
        self.assertEqual(message.customer, other)
        message.sender_phone = "+4915123456787"
        message.save()
        self.assertIsNone(message.customer)

    def test_explicit_manual_assignment_is_preserved(self):
        other = Customer.data.create(address="Manuell ausgewählter Kunde")
        message = WhatsAppMessage.data.create(
            sender="Kunde", sender_phone=self.customer.whatsapp_phone,
            text="Bestellung", customer=other,
        )
        message.text = "Bestellung ergänzt"
        message.save()
        message.refresh_from_db()
        self.assertEqual(message.customer, other)

    def test_customer_api_normalizes_phone_and_allows_clearing_it(self):
        url = reverse("customer-detail", args=[self.customer.pk])
        response = self.client.patch(url, {"whatsapp_phone": "0049 151 2345-6789"}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["whatsapp_phone"], "+4915123456789")
        response = self.client.patch(url, {"whatsapp_phone": ""}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["whatsapp_phone"], "")

    def test_invalid_phone_input_returns_errors_without_changing_customer(self):
        url = reverse("customer-detail", args=[self.customer.pk])
        for phone in ("0151 23456789", "abc", "()--", "+49abc15123456789", "+1234567890123456", {"phone": "abc"}):
            with self.subTest(phone=phone):
                response = self.client.patch(url, {"whatsapp_phone": phone}, format="json")
                self.assertEqual(response.status_code, 400, response.data)
                self.assertIn("whatsapp_phone", response.data)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.whatsapp_phone, "+4915123456789")

    def test_message_admin_form_validates_and_normalizes_phone(self):
        form_class = modelform_factory(WhatsAppMessage, fields=["sender", "sender_phone", "text"])
        form = form_class(data={"sender": "Kunde", "sender_phone": "0151", "text": "Bestellung"})
        self.assertFalse(form.is_valid())
        self.assertIn("sender_phone", form.errors)
        form = form_class(data={"sender": "Kunde", "sender_phone": "0049 151 23456789", "text": "Bestellung"})
        self.assertTrue(form.is_valid(), form.errors)
        message = form.save()
        self.assertEqual(message.sender_phone, self.customer.whatsapp_phone)
        self.assertEqual(message.customer, self.customer)

    def test_invalid_number_is_also_rejected_for_direct_model_writes(self):
        with self.assertRaises(ValidationError):
            WhatsAppMessage.data.create(sender="Kunde", sender_phone="kein Telefon", text="Bestellung")


class WhatsAppIntakeTests(TestCase):
    def setUp(self):
        self.customer = Customer.data.create(address="Beispielkunde", whatsapp_phone="+4915123456789")
        self.received_at = datetime(2026, 10, 8, 12, tzinfo=ZoneInfo("Europe/Berlin"))
        self.text = "  Heute 2x Soljanka.\nMorgen 1x Schnitzel ohne Kartoffeln.\n"
        self.payload = {
            "orders": [
                {"date": "2026-10-08", "name": "Soljanka", "count": 2, "comment": ""},
                {"date": "2026-10-09", "name": "Schnitzel", "count": 1, "comment": "Ohne\nKartoffeln"},
            ],
            "uncertainty": "",
        }
        model = patch("invoices.intake.extract_orders", return_value=self.payload)
        self.model = model.start()
        self.addCleanup(model.stop)

    def create_message(self, **changes):
        return WhatsAppMessage.data.create(**{
            "sender": "Kunde", "sender_phone": self.customer.whatsapp_phone,
            "text": self.text, "received_at": self.received_at, **changes,
        })

    def test_save_creates_unreviewed_days_and_copies_original_with_menu_price(self):
        week = Week.data.create(location=Location.data.create(name="Imbiss"), start=date(2026, 10, 5))
        Plan.data.create(
            day=week.days.get(date=date(2026, 10, 8)),
            meal=Meal.data.create(name="Soljanka"), price=Decimal("5.50"),
        )
        message = self.create_message()
        self.assertIsNotNone(message.processed_at)
        self.assertEqual(message.processing_error, "")
        self.assertEqual(InvoiceDay.data.count(), 2)
        for day in InvoiceDay.data.all():
            self.assertEqual(day.source_message, self.text)
            self.assertFalse(day.reviewed)
            self.assertFalse(day.delivered)
            self.assertEqual(day.customer, self.customer)
        soup = InvoiceMeal.data.get(name="Soljanka")
        self.assertEqual((soup.count, soup.price), (2, Decimal("5.50")))
        schnitzel = InvoiceMeal.data.get(name="Schnitzel")
        self.assertEqual(schnitzel.price, 0)
        self.assertEqual(schnitzel.comment, "Ohne Kartoffeln")
        self.assertTrue(schnitzel.price_needs_review)
        self.assertFalse(soup.price_needs_review)

    def make_choice_menu(self, location="Imbiss"):
        week = Week.data.create(location=Location.data.create(name=location), start=date(2026, 10, 5))
        day = week.days.get(date=date(2026, 10, 9))
        Plan.data.create(day=day, meal=Meal.data.create(name="Schnitzel/Cordon Bleu oder Gemüseschnitzel", headline=True), price=0, order=1)
        Plan.data.create(day=day, meal=Meal.data.create(name="- mit Blumenkohl und Kartoffelgratin"), price=9, order=3)
        Plan.data.create(day=day, meal=Meal.data.create(name="- mit Letscho und Kartoffeln"), price=8, order=2)
        return day

    def test_choice_menu_defaults_to_first_side_and_keeps_special_request(self):
        self.make_choice_menu()
        self.create_message()
        meal = InvoiceMeal.data.get(day__date=date(2026, 10, 9))
        self.assertEqual(meal.name, "Schnitzel mit Letscho und Kartoffeln")
        self.assertEqual(meal.price, Decimal("8.00"))
        self.assertEqual(meal.comment, "Ohne Kartoffeln")
        self.assertTrue(meal.price_needs_review)

    def test_choice_menu_honors_main_dish_and_explicit_side(self):
        self.make_choice_menu()
        for main in ("Schnitzel", "Cordon Bleu", "Gemüseschnitzel"):
            with self.subTest(main=main):
                name, price, needs_review = resolve_menu_order(date(2026, 10, 9), f"{main} mit Blumenkohl", "")
                self.assertEqual(name, f"{main} mit Blumenkohl und Kartoffelgratin")
                self.assertEqual(price, Decimal("9.00"))
                self.assertTrue(needs_review)
        name = "Cordon Bleu mit Blumenkohl und Kartoffelgratin"
        self.assertEqual(resolve_menu_order(date(2026, 10, 9), name, ""), (name, Decimal("9.00"), False))

    def test_unknown_side_is_not_replaced_with_default(self):
        self.make_choice_menu()
        self.assertEqual(resolve_menu_order(date(2026, 10, 9), "Schnitzel mit Reis", ""), ("Schnitzel mit Reis", 0, True))

    def test_explicit_side_in_special_request_overrides_default(self):
        self.make_choice_menu()
        self.assertEqual(
            resolve_menu_order(date(2026, 10, 9), "Schnitzel", "mit Blumenkohl, ohne Kartoffelgratin"),
            ("Schnitzel mit Blumenkohl und Kartoffelgratin", Decimal("9.00"), True),
        )

    def test_choice_menu_does_not_take_sides_from_another_group(self):
        day = self.make_choice_menu()
        day.plans.filter(meal__side_dish=True).delete()
        Plan.data.create(day=day, meal=Meal.data.create(name="Tagessuppe"), price=5, order=2)
        Plan.data.create(day=day, meal=Meal.data.create(name="- mit Brot"), price=2, order=3)
        self.assertEqual(resolve_menu_order(day.date, "Schnitzel", ""), ("Schnitzel", 0, True))

    def test_conflicting_choice_menu_prices_are_not_guessed(self):
        self.make_choice_menu("Imbiss A")
        other = self.make_choice_menu("Imbiss B")
        other.plans.filter(order=2).update(price=10)
        self.assertEqual(resolve_menu_order(other.date, "Schnitzel", ""), ("Schnitzel", 0, True))

    def test_repeated_saves_and_stale_instance_do_not_duplicate_orders(self):
        message = self.create_message()
        stale = WhatsAppMessage.data.get(pk=message.pk)
        stale.processed_at = None
        message.save()
        stale.save()
        self.assertEqual(InvoiceDay.data.count(), 2)
        self.assertEqual(InvoiceMeal.data.count(), 2)
        self.assertEqual(self.model.call_count, 1)
        self.assertIsNotNone(stale.processed_at)

    def test_conflicting_menu_prices_require_manual_price_review(self):
        meal = Meal.data.create(name="Soljanka")
        for location, price in (("Imbiss A", "5.50"), ("Imbiss B", "6.00")):
            week = Week.data.create(location=Location.data.create(name=location), start=date(2026, 10, 5))
            Plan.data.create(day=week.days.get(date=date(2026, 10, 8)), meal=meal, price=Decimal(price))
        self.create_message()
        soup = InvoiceMeal.data.get(name="Soljanka")
        self.assertEqual(soup.price, 0)
        self.assertTrue(soup.price_needs_review)
        self.assertEqual(soup.comment, "")

    def test_later_message_preserves_orders_and_source_of_previous_message(self):
        self.create_message()
        self.create_message(text="Zusätzlich morgen 1x Schnitzel")
        self.assertEqual(InvoiceDay.data.count(), 4)
        self.assertEqual(InvoiceDay.data.filter(source_message=self.text).count(), 2)

    def test_missing_customer_waits_until_manual_assignment(self):
        message = self.create_message(sender_phone="")
        self.model.assert_not_called()
        self.assertIn("Kunden zuordnen", message.processing_error)
        self.assertFalse(InvoiceDay.data.exists())
        message.customer = self.customer
        message.save()
        self.assertEqual(InvoiceDay.data.count(), 2)

    def test_model_failure_keeps_message_and_retry_creates_orders_once(self):
        self.model.side_effect = IntakeError("Lokale KI nicht erreichbar")
        message = self.create_message()
        self.assertTrue(WhatsAppMessage.data.filter(pk=message.pk).exists())
        self.assertIsNone(message.processed_at)
        self.assertIn("KI nicht erreichbar", message.processing_error)
        self.assertFalse(InvoiceDay.data.exists())
        self.model.side_effect = None
        message.save()
        self.assertEqual(InvoiceDay.data.count(), 2)
        self.assertEqual(message.processing_error, "")

    def test_invalid_or_ambiguous_result_creates_no_partial_orders(self):
        for change in ({"date": "irgendwann"}, {"count": 0}, {"count": -1}, {"name": ""}):
            with self.subTest(change=change):
                self.model.return_value = {
                    "orders": [self.payload["orders"][0], {**self.payload["orders"][1], **change}],
                    "uncertainty": "",
                }
                message = self.create_message()
                self.assertIsNone(message.processed_at)
                self.assertTrue(message.processing_error)
                self.assertFalse(InvoiceDay.data.exists())
        self.model.return_value = {"orders": [], "uncertainty": "Welcher Mittwoch ist gemeint?"}
        message = self.create_message()
        self.assertEqual(message.processing_error, "Welcher Mittwoch ist gemeint?")
        self.assertFalse(InvoiceDay.data.exists())

    def test_changing_processed_message_does_not_overwrite_reviewed_orders(self):
        message = self.create_message()
        InvoiceDay.data.update(reviewed=True)
        message.text = "Bitte ganz andere Gerichte"
        message.save()
        self.assertEqual(InvoiceDay.data.count(), 2)
        self.assertEqual(InvoiceDay.data.filter(reviewed=True, source_message=self.text).count(), 2)
        self.assertEqual(self.model.call_count, 1)

    def test_two_positions_on_same_date_create_one_day(self):
        self.payload["orders"][1]["date"] = "2026-10-08"
        self.create_message()
        self.assertEqual(InvoiceDay.data.count(), 1)
        self.assertEqual(InvoiceMeal.data.count(), 2)

    def test_new_orders_appear_as_provisional_in_delivery_overview(self):
        self.payload["orders"][0]["date"] = localdate().isoformat()
        self.create_message()
        client = APIClient()
        deliveries = client.get(reverse("invoiceday-deliveries")).data
        self.assertTrue(deliveries)
        self.assertTrue(all(not day["reviewed"] for day in deliveries))
        day = InvoiceDay.data.get(date=localdate())
        response = client.patch(reverse("invoiceday-detail", args=[day.pk]), {"reviewed": True}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in client.get(reverse("invoiceday-today")).data], [day.pk])

    @patch("invoices.intake.requests.post")
    def test_extractor_uses_received_date_and_validates_model_response(self, post):
        message = self.create_message(sender_phone="")
        post.return_value.json.return_value = {"message": {"content": '{"orders": [], "uncertainty": "Datum fehlt"}'}}
        self.assertEqual(extract_orders(message)["uncertainty"], "Datum fehlt")
        prompt = post.call_args.kwargs["json"]["messages"][0]["content"]
        self.assertIn("2026-10-08", prompt)
        self.assertEqual(post.call_args.kwargs["json"]["messages"][1]["content"], self.text)
        post.side_effect = requests.Timeout()
        with self.assertRaises(IntakeError):
            extract_orders(message)
        post.side_effect = None
        post.return_value.json.return_value = {"message": {"content": "Kein JSON"}}
        with self.assertRaises(IntakeError):
            extract_orders(message)
