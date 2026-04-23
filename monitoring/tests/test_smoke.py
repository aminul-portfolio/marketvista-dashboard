from django.contrib.auth import get_user_model
from django.core.management import call_command, get_commands
from django.test import TestCase
from django.urls import reverse

from monitoring.models import Alert, Asset, MarketSignal, PriceOHLC, PriceSnapshot, WatchlistItem


User = get_user_model()


class TestMarketVistaSmoke(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="smoke_user",
            password="testpass123",
        )

    def _run_seed_demo(self):
        commands = get_commands()

        if "seed_demo" in commands:
            call_command("seed_demo")
            return

        if "seed_demo_data" in commands:
            call_command("seed_demo_data")
            return

        self.fail("No seed command found. Expected 'seed_demo' or 'seed_demo_data'.")

    def test_home_page_loads(self):
        response = self.client.get(reverse("monitoring:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MarketVista")

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("monitoring:dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("monitoring:login"), response.url)

    def test_seed_demo_populates_core_models(self):
        self._run_seed_demo()

        self.assertGreater(Asset.objects.count(), 0)
        self.assertGreater(PriceOHLC.objects.count(), 0)
        self.assertGreater(PriceSnapshot.objects.count(), 0)
        self.assertGreater(MarketSignal.objects.count(), 0)
        self.assertGreater(Alert.objects.count(), 0)
        self.assertGreater(WatchlistItem.objects.count(), 0)

    def test_seed_demo_is_repeatable(self):
        self._run_seed_demo()
        first_counts = {
            "assets": Asset.objects.count(),
            "ohlc": PriceOHLC.objects.count(),
            "snapshots": PriceSnapshot.objects.count(),
            "signals": MarketSignal.objects.count(),
            "alerts": Alert.objects.count(),
            "watchlist": WatchlistItem.objects.count(),
        }

        self._run_seed_demo()
        second_counts = {
            "assets": Asset.objects.count(),
            "ohlc": PriceOHLC.objects.count(),
            "snapshots": PriceSnapshot.objects.count(),
            "signals": MarketSignal.objects.count(),
            "alerts": Alert.objects.count(),
            "watchlist": WatchlistItem.objects.count(),
        }

        self.assertEqual(first_counts, second_counts)

    def test_dashboard_loads_for_logged_in_user_after_seed(self):
        self._run_seed_demo()
        self.client.force_login(self.user)

        response = self.client.get(reverse("monitoring:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard")

    def test_ohlc_api_returns_seeded_data(self):
        self._run_seed_demo()
        self.client.force_login(self.user)

        asset = Asset.objects.order_by("symbol").first()
        self.assertIsNotNone(asset)

        response = self.client.get(
            reverse("monitoring:ohlc_data"),
            {"symbol": asset.symbol},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertIn("ohlc", payload)
        self.assertGreater(len(payload["ohlc"]), 0)
        self.assertIn("last_updated", payload)
        self.assertIn("server_time", payload)

    def test_price_api_returns_seeded_snapshots(self):
        self._run_seed_demo()
        self.client.force_login(self.user)

        response = self.client.get(reverse("monitoring:price_data"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertIn("snapshots", payload)
        self.assertGreater(len(payload["snapshots"]), 0)
        self.assertIn("symbol", payload["snapshots"][0])
        self.assertIn("price", payload["snapshots"][0])

    def test_signals_page_loads_after_seed(self):
        self._run_seed_demo()
        self.client.force_login(self.user)

        response = self.client.get(reverse("monitoring:signals"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Signals")