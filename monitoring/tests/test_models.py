from datetime import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from monitoring.models import Alert, Asset, MarketSignal, PriceOHLC, PriceSnapshot, WatchlistItem


User = get_user_model()


class TestMonitoringModels(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="model_user",
            password="testpass123",
        )
        cls.asset = Asset.objects.create(
            symbol="BTC/USD",
            name="Bitcoin",
            asset_type="crypto",
        )

    def test_asset_string_representation(self):
        self.assertEqual(str(self.asset), "BTC/USD (Cryptocurrency)")

    def test_price_snapshot_save_makes_naive_timestamp_aware(self):
        snapshot = PriceSnapshot.objects.create(
            asset=self.asset,
            price=Decimal("101.25"),
            timestamp=datetime(2026, 4, 23, 10, 30, 0),  # naive
        )
        snapshot.refresh_from_db()

        self.assertTrue(timezone.is_aware(snapshot.timestamp))
        self.assertEqual(snapshot.asset, self.asset)

    def test_price_ohlc_save_makes_naive_timestamp_aware(self):
        candle = PriceOHLC.objects.create(
            asset=self.asset,
            timestamp=datetime(2026, 4, 23, 9, 0, 0),  # naive
            open=Decimal("100.00"),
            high=Decimal("105.00"),
            low=Decimal("99.00"),
            close=Decimal("104.00"),
            volume=Decimal("1200.00"),
            source="yahoo",
        )
        candle.refresh_from_db()

        self.assertTrue(timezone.is_aware(candle.timestamp))
        self.assertEqual(candle.source, "yahoo")

    def test_watchlist_item_unique_per_user_asset(self):
        WatchlistItem.objects.create(
            user=self.user,
            asset=self.asset,
            note="Primary monitoring asset",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                WatchlistItem.objects.create(
                    user=self.user,
                    asset=self.asset,
                    note="Duplicate item",
                )

    def test_alert_string_representation(self):
        alert = Alert.objects.create(
            user=self.user,
            asset=self.asset,
            direction="above",
            target_price=Decimal("120000.00"),
        )

        self.assertIn("BTC/USD", str(alert))
        self.assertIn("above", str(alert))

    def test_market_signal_string_representation(self):
        signal = MarketSignal.objects.create(
            asset=self.asset,
            signal_type="pct_move_3d",
            severity="ELEVATED",
            title="3-day move +8.50%",
            details="Asset moved sharply higher.",
            metric_value=Decimal("8.50"),
            signal_timestamp=timezone.now(),
        )

        signal_text = str(signal)
        self.assertIn("BTC/USD", signal_text)
        self.assertIn("ELEVATED", signal_text)

    def test_price_snapshot_ordering_newest_first(self):
        older = PriceSnapshot.objects.create(
            asset=self.asset,
            price=Decimal("100.00"),
            timestamp=timezone.now() - timezone.timedelta(hours=2),
        )
        newer = PriceSnapshot.objects.create(
            asset=self.asset,
            price=Decimal("105.00"),
            timestamp=timezone.now(),
        )

        snapshots = list(PriceSnapshot.objects.filter(asset=self.asset))
        self.assertEqual(snapshots[0], newer)
        self.assertEqual(snapshots[1], older)