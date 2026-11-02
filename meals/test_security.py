from datetime import date
from html.parser import HTMLParser

import pendulum
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from meals.models import Day, Location, Meal, Plan, Week
from meals.utils import get_or_create_week


class TemplateTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.protected_text = []

    def handle_starttag(self, tag, attrs):
        if tag not in {
            "area",
            "base",
            "br",
            "col",
            "embed",
            "hr",
            "img",
            "input",
            "link",
            "meta",
            "param",
            "source",
            "track",
            "wbr",
        }:
            self.stack.append((tag, "v-pre" in dict(attrs)))

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        if "{{ 6 * 7 }}" in data:
            self.protected_text.append(any(pre for _, pre in self.stack))


class MenuAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().data.create_user(username="menu-editor")
        cls.location = Location.data.get(pk=1)
        cls.week = get_or_create_week(date(2026, 8, 10), cls.location)
        cls.week.published = True
        cls.week.save(update_fields=["published"])
        cls.day = cls.week.days.first()
        cls.meal = Meal.data.create(name="Kartoffelsuppe")
        cls.plan = Plan.data.create(day=cls.day, meal=cls.meal, price=5)

    def setUp(self):
        self.client = APIClient()

    def resources(self):
        return (
            ("week", self.week.pk),
            ("day", self.day.pk),
            ("meal", self.meal.pk),
            ("plan", self.plan.pk),
        )

    def test_anonymous_menu_writes_are_denied(self):
        before = {model: model.data.count() for model in (Week, Day, Meal, Plan)}
        for name, pk in self.resources():
            requests = [("post", reverse(f"{name}-list"))]
            requests.extend(
                (method, reverse(f"{name}-detail", args=[pk]))
                for method in ("put", "patch", "delete")
            )
            for method, url in requests:
                with self.subTest(method=method, url=url):
                    response = getattr(self.client, method)(url, {}, format="json")
                    self.assertEqual(response.status_code, 403)
        for model, count in before.items():
            self.assertEqual(model.data.count(), count)

    def test_public_menu_reads_remain_available(self):
        for name, pk in self.resources():
            for url in (reverse(f"{name}-list"), reverse(f"{name}-detail", args=[pk])):
                with self.subTest(url=url):
                    self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(
            self.client.get("/api/weeks/get-week/", {"date": "2026-08-10"}).status_code,
            200,
        )
        self.assertContains(
            self.client.get("/", {"date": "2026-08-10"}), "Kartoffelsuppe"
        )
        get_or_create_week(
            pendulum.today().add(days=7).start_of("week").date(), self.location
        )
        self.assertEqual(self.client.get("/today").status_code, 200)

    def test_public_read_does_not_create_missing_weeks_or_days(self):
        before = (Week.data.count(), Day.data.count())
        response = self.client.get("/api/weeks/get-week/", {"date": "2036-01-07"})
        self.assertEqual(response.status_code, 404)
        response = self.client.get("/api/weeks/current-week/")
        self.assertEqual(response.status_code, 404)
        response = self.client.get("/", {"date": "2036-01-07"})
        self.assertContains(
            response, "Der Speiseplan dieser Woche ist noch nicht fertig."
        )
        self.assertEqual((Week.data.count(), Day.data.count()), before)

    def test_session_login_allows_editing_and_creating_weeks(self):
        self.client.force_login(self.user)
        for name, pk, payload in (
            ("week", self.week.pk, {"footer": "<p>Hinweis</p>"}),
            ("day", self.day.pk, {"closed": True}),
            ("meal", self.meal.pk, {"name": "Gemüsesuppe"}),
            ("plan", self.plan.pk, {"price": "6.00"}),
        ):
            with self.subTest(resource=name):
                response = self.client.patch(
                    reverse(f"{name}-detail", args=[pk]), payload, format="json"
                )
                self.assertEqual(response.status_code, 200)
        before = (Week.data.count(), Day.data.count())
        response = self.client.get("/api/weeks/get-week/", {"date": "2036-01-07"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            (Week.data.count(), Day.data.count()), (before[0] + 1, before[1] + 5)
        )
        self.client.logout()
        self.assertEqual(
            self.client.patch(
                reverse("meal-detail", args=[self.meal.pk]), {}
            ).status_code,
            403,
        )

    def test_invalid_rich_text_input_returns_validation_errors(self):
        self.client.force_login(self.user)
        for name, pk, field in (
            ("day", self.day.pk, "alt_text"),
            ("week", self.week.pk, "footer"),
        ):
            for value in (None, {}, []):
                with self.subTest(resource=name, value=value):
                    response = self.client.patch(
                        reverse(f"{name}-detail", args=[pk]),
                        {field: value},
                        format="json",
                    )
                    self.assertEqual(response.status_code, 400)
                    self.assertIn(field, response.data)

    def test_api_and_public_html_remove_stored_active_content(self):
        payload = (
            '<p><strong style="color: rgb(230, 0, 0);" onclick="probe()">Geschlossen</strong></p>'
            '<script type="application/json" id="security-probe">"probe"</script>'
        )
        self.day.closed = True
        self.day.alt_text = payload
        self.day.save()
        self.location.headline = payload
        self.location.save()
        self.week.footer = payload
        self.week.save()
        responses = (
            self.client.get(reverse("day-detail", args=[self.day.pk])).content.decode(),
            self.client.get(
                reverse("week-detail", args=[self.week.pk])
            ).content.decode(),
            self.client.get("/", {"date": "2026-08-10"}).content.decode(),
        )
        for output in responses:
            with self.subTest(output=output[:80]):
                self.assertNotIn("security-probe", output)
                self.assertNotIn("onclick", output)
                self.assertIn("Geschlossen", output)

    def test_public_text_cannot_be_interpreted_as_a_vue_template(self):
        marker = "{{ 6 * 7 }}"
        self.meal.name = marker
        self.meal.save()
        self.day.closed = True
        self.day.alt_text = f"<p>{marker}</p>"
        self.day.save()
        self.week.special_menu = self.plan
        self.week.save()
        Plan.data.create(day=self.week.days.last(), meal=self.meal, price=5)
        self.location.headline = f"<p>{marker}</p>"
        self.location.save()
        html = self.client.get("/", {"date": "2026-08-10"}).content.decode()
        parser = TemplateTextParser()
        parser.feed(html)
        self.assertEqual(len(parser.protected_text), 8)
        self.assertTrue(all(parser.protected_text))


class MenuHtmlSafetyTests(SimpleTestCase):
    def test_existing_formatting_is_preserved(self):
        value = '<p class="ql-align-center"><strong style="color: rgb(230, 0, 0);">Geschlossen</strong><br><em>Hinweis</em></p>'
        for cleaned in (
            Day(alt_text=value).safe_alt_text,
            Week(footer=value).safe_footer,
            Location(headline=value).safe_headline,
        ):
            self.assertIn('class="ql-align-center"', cleaned)
            self.assertIn("rgb(230, 0, 0)", cleaned)
            self.assertIn("<em>Hinweis</em>", cleaned)

    def test_active_tags_attributes_styles_and_links_are_removed(self):
        payload = (
            '<script>probe()</script><svg onload="probe()"></svg>'
            '<iframe src="https://example.com"></iframe>'
            '<p onclick="probe()" v-html="probe()" style="color:red;position:fixed;background-image:url(https://example.com)">Text</p>'
            '<a href="javascript:probe()">Link</a><a href="data:text/html,probe">Data</a>'
        )
        for cleaned in (
            Day(alt_text=payload).safe_alt_text,
            Week(footer=payload).safe_footer,
            Location(headline=payload).safe_headline,
        ):
            for forbidden in (
                "script",
                "svg",
                "iframe",
                "onclick",
                "v-html",
                "position",
                "background-image",
                "javascript:",
                "data:text",
            ):
                with self.subTest(forbidden=forbidden):
                    self.assertNotIn(forbidden, cleaned)
            self.assertIn("Text", cleaned)

    def test_safe_background_images_survive_but_dangerous_urls_do_not(self):
        image = "data:image/jpeg;base64,/9j/2Q=="
        value = f'<p><img onerror="probe()" src="{image}"></p>'
        self.assertEqual(Week(footer=value).background, image)
        self.assertEqual(Day(alt_text=value).background, image)
        self.assertNotIn("<img", Day(alt_text=value).safe_alt_text)
        self.assertNotIn("<img", Week(footer=value).safe_footer)
        for url in (
            "javascript:probe()",
            "data:text/html,probe",
            "data:image/svg+xml;base64,PHN2Zz4=",
            "ftp://example.com/a.jpg",
        ):
            with self.subTest(url=url):
                value = f'<img src="{url}" onerror="probe()">'
                self.assertIsNone(Week(footer=value).background)
                self.assertIsNone(Day(alt_text=value).background)

    def test_empty_and_malformed_html_are_handled(self):
        self.assertEqual(Day(alt_text="").safe_alt_text, "")
        self.assertIsNone(Week(footer="").background)
        cleaned = Day(
            alt_text="<p><strong>Hinweis<svg><script>probe()</script>"
        ).safe_alt_text
        self.assertIn("Hinweis", cleaned)
        self.assertNotIn("script", cleaned)
