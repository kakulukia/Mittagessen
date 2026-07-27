from datetime import date

from django.test import TestCase
from django.urls import reverse

from meals.models import Location, LocationHeadlineRevision, Meal, Plan
from meals.utils import get_or_create_week
from users.models import User


class LocationHeadlineRevisionAdminTest(TestCase):
    def setUp(self):
        self.user = User.data.create_superuser(
            username="admin", email="admin@example.com", password="secret"
        )
        self.client.force_login(self.user)
        self.original = "<p><strong>Heute &amp; morgen</strong></p>"
        self.changed = '<p style="color: red">Nur heute geöffnet</p>'
        self.location = Location.data.create(
            name="Emmas Imbiss", headline=self.original
        )
        self.original_revision = LocationHeadlineRevision.objects.create(
            location=self.location, headline=self.original
        )

    def test_admin_edit_and_restore_keep_both_versions(self):
        response = self.client.post(
            reverse("admin:meals_location_change", args=[self.location.pk]),
            {
                "name": self.location.name,
                "headline": self.changed,
                "logo": "",
                "_save": "Speichern",
            },
        )

        self.assertEqual(response.status_code, 302)
        changed_revision = self.location.headline_revisions.get(headline=self.changed)
        self.assertEqual(changed_revision.created_by, self.user)
        history_url = reverse("admin:meals_location_history", args=[self.location.pk])

        response = self.client.get(history_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Überschriftsversionen")
        self.assertContains(response, "Nur heute geöffnet")
        self.assertGreater(response.context["action_list"].paginator.count, 0)

        response = self.client.post(
            history_url,
            {
                "headline_revision": [
                    self.original_revision.pk,
                    changed_revision.pk,
                ],
            },
        )

        self.assertEqual(response.status_code, 302)
        self.location.refresh_from_db()
        self.assertEqual(self.location.headline, self.changed)

        response = self.client.post(
            history_url,
            {
                "headline_revision": [self.original_revision.pk],
            },
        )

        self.assertEqual(response.status_code, 302)
        self.location.refresh_from_db()
        self.assertEqual(self.location.headline, self.original)
        self.assertTrue(
            self.location.headline_revisions.filter(pk=changed_revision.pk).exists()
        )
        self.assertEqual(
            self.location.headline_revisions.filter(headline=self.original).count(), 2
        )


class SingleLocationTest(TestCase):
    def test_week_and_dayless_plan_need_no_second_location(self):
        Location.data.all().delete()
        location = Location.data.create(id=1, name="Emmas Imbiss")
        week = get_or_create_week(date(2026, 7, 27), location)
        meal = Meal.data.create(name="Kartoffelsuppe")

        dayless_plan = Plan.data.create(meal=meal, price=0)
        response = self.client.get("/api/weeks/get-week/", {"date": "2026-07-27"})

        self.assertEqual(Location.data.count(), 1)
        self.assertEqual(week.location, location)
        self.assertEqual(dayless_plan.price, 0)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.client.get("/api/weeks/copy-menu/", {"date": "2026-07-27"}).status_code,
            404,
        )
