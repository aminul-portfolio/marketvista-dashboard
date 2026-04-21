from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from monitoring.models import Asset, MarketSignal, PriceOHLC, PriceSnapshot, WatchlistItem


class MarketVistaSmokeTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.superuser = self.user_model.objects.create_superuser(
            username="adminuser",
            email="admin@example.com",
            password="adminpass123",
        )

    def test_home_page_loads(self):
        response = self.client.get(reverse("monitoring:home"))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("monitoring:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_seed_demo_data_populates_core_models(self):
        call_command("seed_demo_data")

        self.assertEqual(Asset.objects.count(), 2)
        self.assertEqual(PriceOHLC.objects.count(), 50)
        self.assertEqual(PriceSnapshot.objects.count(), 2)
        self.assertGreaterEqual(MarketSignal.objects.count(), 1)
        self.assertGreaterEqual(WatchlistItem.objects.count(), 1)

    def test_dashboard_loads_for_logged_in_user_after_seed(self):
        call_command("seed_demo_data")
        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(reverse("monitoring:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MarketVista Dashboard")
        self.assertContains(response, "Latest Signals")
        self.assertContains(response, "Operational Status")

    def test_ohlc_api_returns_seeded_data(self):
        call_command("seed_demo_data")
        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(
            reverse("monitoring:ohlc_data"),
            {"symbol": "BTC/USD"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("ohlc", payload)
        self.assertGreater(len(payload["ohlc"]), 0)