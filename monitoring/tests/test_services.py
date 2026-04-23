from decimal import Decimal

from django import forms
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from monitoring.models import Alert, Asset, MarketSignal, PriceOHLC, PriceSnapshot
from monitoring.services.alerts import (
    create_user_alert_from_form,
    fetch_and_acknowledge_triggered_alerts,
    get_active_alert_count,
)
from monitoring.services.market import build_dashboard_context, get_freshness_signal
from monitoring.services.signals import compute_asset_signals, refresh_asset_signals
from monitoring.services.watchlist import (
    add_asset_to_watchlist,
    get_watchlist_for_user,
    remove_asset_from_watchlist,
)


User = get_user_model()


class AlertTestForm(forms.ModelForm):
    class Meta:
        model = Alert
        fields = ["asset", "direction", "target_price"]


class TestMonitoringServices(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="service_user",
            password="testpass123",
        )
        self.asset = Asset.objects.create(
            symbol="BTC/USD",
            name="Bitcoin",
            asset_type="crypto",
        )
        self.second_asset = Asset.objects.create(
            symbol="ETH/USD",
            name="Ethereum",
            asset_type="crypto",
        )

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

    def test_get_freshness_signal_returns_no_data_when_empty(self):
        freshness = get_freshness_signal()

        self.assertEqual(freshness["status"], "stale")
        self.assertEqual(freshness["label"], "No market data loaded")
        self.assertIsNone(freshness["delay_minutes"])

    def test_get_freshness_signal_returns_fresh_for_recent_snapshot(self):
        PriceSnapshot.objects.create(
            asset=self.asset,
            price=Decimal("101.50"),
            timestamp=timezone.now() - timezone.timedelta(minutes=5),
        )

        freshness = get_freshness_signal()

        self.assertEqual(freshness["status"], "fresh")
        self.assertEqual(freshness["label"], "Fresh market data")
        self.assertLessEqual(freshness["delay_minutes"], 15)

    def test_watchlist_services_add_get_and_remove(self):
        item = add_asset_to_watchlist(self.user, self.asset, note="Core asset")
        watchlist = list(get_watchlist_for_user(self.user))

        self.assertEqual(len(watchlist), 1)
        self.assertEqual(watchlist[0], item)
        self.assertEqual(watchlist[0].note, "Core asset")

        deleted_count = remove_asset_from_watchlist(self.user, self.asset)
        self.assertEqual(deleted_count, 1)
        self.assertEqual(get_watchlist_for_user(self.user).count(), 0)

    def test_alert_services_create_and_acknowledge_triggered_alerts(self):
        form = AlertTestForm(
            data={
                "asset": self.asset.pk,
                "direction": "above",
                "target_price": "120000.00",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

        alert = create_user_alert_from_form(self.user, form)
        self.assertEqual(alert.user, self.user)
        self.assertEqual(get_active_alert_count(self.user), 1)

        PriceSnapshot.objects.create(
            asset=self.asset,
            price=Decimal("121000.00"),
            timestamp=timezone.now(),
        )

        alert.is_triggered = True
        alert.save(update_fields=["is_triggered"])

        payload = fetch_and_acknowledge_triggered_alerts(self.user)

        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["symbol"], "BTC/USD")
        self.assertEqual(payload[0]["direction"], "above")

        alert.refresh_from_db()
        self.assertTrue(alert.is_notified)

    def test_compute_asset_signals_returns_expected_types(self):
        closes = [
            100.00, 100.20, 99.80, 100.10, 99.90,
            100.00, 100.10, 99.90, 100.05, 99.95,
            100.00, 100.10, 99.90, 100.00, 100.05,
            99.95, 100.00, 104.00, 110.00, 118.00, 130.00,
        ]
        self._create_ohlc_series(self.asset, closes)

        signals = compute_asset_signals(self.asset)
        signal_types = {signal["signal_type"] for signal in signals}

        self.assertIn("pct_move_3d", signal_types)
        self.assertGreaterEqual(len(signal_types), 1)

    def test_refresh_asset_signals_persists_and_deactivates_old_signal(self):
        old_timestamp = timezone.now() - timezone.timedelta(days=3)
        old_signal = MarketSignal.objects.create(
            asset=self.asset,
            signal_type="pct_move_3d",
            severity="WATCHLIST",
            title="Old move signal",
            details="Old signal that should be deactivated.",
            metric_value=Decimal("3.10"),
            signal_timestamp=old_timestamp,
            is_active=True,
        )

        closes = [
            100.00, 100.20, 99.80, 100.10, 99.90,
            100.00, 100.10, 99.90, 100.05, 99.95,
            100.00, 100.10, 99.90, 100.00, 100.05,
            99.95, 100.00, 104.00, 110.00, 118.00, 130.00,
        ]
        self._create_ohlc_series(self.asset, closes)

        created = refresh_asset_signals(self.asset)

        self.assertGreaterEqual(len(created), 1)

        old_signal.refresh_from_db()
        self.assertFalse(old_signal.is_active)

        active_pct_move = MarketSignal.objects.filter(
            asset=self.asset,
            signal_type="pct_move_3d",
            is_active=True,
        )
        self.assertEqual(active_pct_move.count(), 1)

    def test_build_dashboard_context_returns_expected_summary(self):
        add_asset_to_watchlist(self.user, self.asset, note="Priority asset")

        Alert.objects.create(
            user=self.user,
            asset=self.asset,
            direction="above",
            target_price=Decimal("120000.00"),
            is_triggered=False,
        )

        PriceSnapshot.objects.create(
            asset=self.asset,
            price=Decimal("101.00"),
            timestamp=timezone.now(),
        )
        PriceSnapshot.objects.create(
            asset=self.second_asset,
            price=Decimal("201.00"),
            timestamp=timezone.now(),
        )

        self._create_ohlc_series(self.asset, [100, 101, 102, 103, 110])
        self._create_ohlc_series(self.second_asset, [200, 201, 202, 203, 204])

        MarketSignal.objects.create(
            asset=self.asset,
            signal_type="pct_move_3d",
            severity="ELEVATED",
            title="3-day move +8%",
            details="Strong move",
            metric_value=Decimal("8.00"),
            signal_timestamp=timezone.now(),
            is_active=True,
        )

        context = build_dashboard_context(self.user, refresh_signals=False)

        self.assertEqual(context["tracked_assets_count"], 2)
        self.assertEqual(context["active_alerts_count"], 1)
        self.assertEqual(context["total_alerts"], 1)
        self.assertEqual(len(context["watchlist_items"]), 1)
        self.assertIsNotNone(context["freshness_signal"])
        self.assertIsNotNone(context["top_mover"])