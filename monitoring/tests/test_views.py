from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from monitoring.models import Alert, Asset, MarketSignal, PriceOHLC, PriceSnapshot, WatchlistItem
from monitoring.services.signals import refresh_asset_signals


User = get_user_model()


class TestMonitoringViews(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="view_user",
            password="testpass123",
        )
        self.asset = Asset.objects.create(
            symbol="BTC/USD",
            name="Bitcoin",
            asset_type="crypto",
        )

        self._create_ohlc_series(
            self.asset,
            [
                100.00, 100.20, 99.80, 100.10, 99.90,
                100.00, 100.10, 99.90, 100.05, 99.95,
                100.00, 100.10, 99.90, 100.00, 100.05,
                99.95, 100.00, 104.00, 110.00, 118.00, 130.00,
            ],
        )

        PriceSnapshot.objects.create(
            asset=self.asset,
            price=Decimal("130.00"),
            open=Decimal("118.00"),
            high=Decimal("131.00"),
            low=Decimal("117.50"),
            close=Decimal("130.00"),
            volume=Decimal("1550.00"),
            timestamp=timezone.now(),
        )

        Alert.objects.create(
            user=self.user,
            asset=self.asset,
            direction="above",
            target_price=Decimal("120.00"),
            is_triggered=False,
        )

        WatchlistItem.objects.create(
            user=self.user,
            asset=self.asset,
            note="Priority asset",
        )

        refresh_asset_signals(self.asset)

    def _create_ohlc_series(self, asset, closes):
        base_time = timezone.now() - timezone.timedelta(days=len(closes))
        for index, close_value in enumerate(closes):
            close_decimal = Decimal(str(close_value))
            PriceOHLC.objects.create(
                asset=asset,
                timestamp=base_time + timezone.timedelta(days=index),
                open=close_decimal - Decimal("1"),
                high=close_decimal + Decimal("2"),
                low=close_decimal - Decimal("2"),
                close=close_decimal,
                volume=Decimal("1000.00") + Decimal(str(index * 10)),
                source="yahoo",
            )

    def test_home_page_loads_for_anonymous_user(self):
        response = self.client.get(reverse("monitoring:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MarketVista")

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("monitoring:dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("monitoring:login"), response.url)

    def test_dashboard_loads_for_logged_in_user(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("monitoring:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard")

    def test_asset_list_loads_for_logged_in_user(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("monitoring:asset_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.asset.symbol)

    def test_asset_detail_loads_for_logged_in_user(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("monitoring:asset_detail", args=[self.asset.symbol])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.asset.symbol)

    def test_watchlist_page_loads_for_logged_in_user(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("monitoring:watchlist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.asset.symbol)

    def test_signals_page_loads_and_filters(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("monitoring:signals"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Signals")

        filtered = self.client.get(
            reverse("monitoring:signals"),
            {"severity": "ELEVATED"},
        )
        self.assertEqual(filtered.status_code, 200)

    def test_alert_list_loads_for_logged_in_user(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("monitoring:alert_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alerts")

    def test_create_alert_post_creates_record(self):
        self.client.force_login(self.user)
        initial_count = Alert.objects.filter(user=self.user).count()

        response = self.client.post(
            reverse("monitoring:create_alert"),
            data={
                "asset": self.asset.pk,
                "direction": "below",
                "target_price": "95.00",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Alert.objects.filter(user=self.user).count(), initial_count + 1)

    def test_watchlist_add_and_remove_views(self):
        second_asset = Asset.objects.create(
            symbol="ETH/USD",
            name="Ethereum",
            asset_type="crypto",
        )
        self.client.force_login(self.user)

        add_response = self.client.post(
            reverse("monitoring:watchlist_add", args=[second_asset.symbol])
        )
        self.assertEqual(add_response.status_code, 302)
        self.assertTrue(
            WatchlistItem.objects.filter(user=self.user, asset=second_asset).exists()
        )

        remove_response = self.client.post(
            reverse("monitoring:watchlist_remove", args=[second_asset.symbol])
        )
        self.assertEqual(remove_response.status_code, 302)
        self.assertFalse(
            WatchlistItem.objects.filter(user=self.user, asset=second_asset).exists()
        )

    def test_price_data_api_returns_snapshot_payload(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("monitoring:price_data"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("snapshots", payload)
        self.assertGreaterEqual(len(payload["snapshots"]), 1)
        self.assertEqual(payload["snapshots"][0]["symbol"], self.asset.symbol)

    def test_ohlc_api_requires_symbol_and_returns_rows(self):
        self.client.force_login(self.user)

        missing_symbol = self.client.get(reverse("monitoring:ohlc_data"))
        self.assertEqual(missing_symbol.status_code, 400)

        valid = self.client.get(
            reverse("monitoring:ohlc_data"),
            {"symbol": self.asset.symbol},
        )
        self.assertEqual(valid.status_code, 200)

        payload = valid.json()
        self.assertIn("ohlc", payload)
        self.assertGreaterEqual(len(payload["ohlc"]), 1)
        self.assertEqual(payload["ohlc"][-1]["close"], float(Decimal("130.00")))

    def test_triggered_alert_appears_in_database_and_signal_exists(self):
        self.assertTrue(
            MarketSignal.objects.filter(asset=self.asset, is_active=True).exists()
        )
        self.assertTrue(
            Alert.objects.filter(user=self.user, asset=self.asset).exists()
        )