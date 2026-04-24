from datetime import timedelta
from decimal import Decimal
from typing import Iterable

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from monitoring.models import Alert, Asset, MarketSignal, PriceOHLC, PriceSnapshot, WatchlistItem
from monitoring.services.signals import refresh_signals_for_assets
from monitoring.services.watchlist import add_asset_to_watchlist


class Command(BaseCommand):
    help = "Seed MarketVista with reviewer-ready demo data."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Resetting MarketVista demo data..."))

        with transaction.atomic():
            # Reset monitoring outputs for a deterministic reviewer-ready state
            MarketSignal.objects.all().delete()
            PriceSnapshot.objects.all().delete()
            PriceOHLC.objects.all().delete()
            Alert.objects.all().delete()

            assets = self._get_or_create_assets()
            base_time = timezone.now() - timedelta(days=44)

            close_series = {
                "BTC/USD": self._build_linear_series(
                    start=103000,
                    segments=[
                        (18, -400),
                        (10, -150),
                        (6, 600),
                        (6, 900),
                        (4, 1600),
                    ],
                ),
                "ETH/USD": self._build_linear_series(
                    start=3400,
                    segments=[
                        (20, -12),
                        (10, 8),
                        (6, 20),
                        (4, 85),
                        (4, 120),
                    ],
                ),
                "XAU/USD": self._build_linear_series(
                    start=2285,
                    segments=[
                        (18, 2),
                        (10, -1),
                        (8, 2),
                        (4, 12),
                        (4, 18),
                    ],
                ),
                "EUR/USD": self._build_linear_series(
                    start=1.1150,
                    segments=[
                        (30, -0.0010),
                        (8, 0.0),
                        (5, 0.0004),
                        (1, 0.0015),
                    ],
                ),
                "US100": self._build_series_from_changes(
                    start=18200,
                    changes=(
                            [12, -8, 10, -6, 9] * 7
                            + [180, -160, 220, -190, 260, -210, 300, -220, 340]
                    ),
                ),
            }

            ohlc_configs = {
                "BTC/USD": {
                    "range_size": Decimal("380"),
                    "base_volume": Decimal("1200"),
                    "source": "demo_seed",
                },
                "ETH/USD": {
                    "range_size": Decimal("42"),
                    "base_volume": Decimal("900"),
                    "source": "demo_seed",
                },
                "XAU/USD": {
                    "range_size": Decimal("8"),
                    "base_volume": Decimal("700"),
                    "source": "demo_seed",
                },
                "EUR/USD": {
                    "range_size": Decimal("0.0022"),
                    "base_volume": Decimal("500"),
                    "source": "demo_seed",
                },
                "US100": {
                    "range_size": Decimal("85"),
                    "base_volume": Decimal("1000"),
                    "source": "demo_seed",
                },
            }

            for symbol, asset in assets.items():
                self._create_ohlc_series_from_closes(
                    asset=asset,
                    base_time=base_time,
                    closes=close_series[symbol],
                    range_size=ohlc_configs[symbol]["range_size"],
                    base_volume=ohlc_configs[symbol]["base_volume"],
                    source=ohlc_configs[symbol]["source"],
                )

            self._refresh_snapshots(assets.values())
            refresh_signals_for_assets(list(assets.values()))

            demo_user = self._get_demo_user()
            if demo_user:
                self._seed_demo_watchlist_and_alerts(demo_user, assets)
                demo_user_label = demo_user.username
            else:
                demo_user_label = "No demo user found"

        active_signal_counts = {
            severity: MarketSignal.objects.filter(is_active=True, severity=severity).count()
            for severity in ("ELEVATED", "WATCHLIST", "INFO")
        }

        self.stdout.write(self.style.SUCCESS("MarketVista demo data seeded successfully."))
        self.stdout.write(f"Assets: {Asset.objects.count()}")
        self.stdout.write(f"OHLC rows: {PriceOHLC.objects.count()}")
        self.stdout.write(f"Snapshots: {PriceSnapshot.objects.count()}")
        self.stdout.write(f"Signals (total): {MarketSignal.objects.count()}")
        self.stdout.write(
            "Active signals → "
            f"ELEVATED: {active_signal_counts['ELEVATED']}, "
            f"WATCHLIST: {active_signal_counts['WATCHLIST']}, "
            f"INFO: {active_signal_counts['INFO']}"
        )
        self.stdout.write(f"Alerts: {Alert.objects.count()}")
        self.stdout.write(f"Watchlist items: {WatchlistItem.objects.count()}")
        self.stdout.write(f"Demo user: {demo_user_label}")

    def _get_or_create_assets(self):
        asset_specs = [
            ("BTC/USD", "Bitcoin", "crypto"),
            ("ETH/USD", "Ethereum", "crypto"),
            ("XAU/USD", "Gold", "commodity"),
            ("EUR/USD", "Euro / US Dollar", "forex"),
            ("US100", "Nasdaq 100", "index"),
        ]

        assets = {}
        for symbol, name, asset_type in asset_specs:
            asset, _ = Asset.objects.get_or_create(
                symbol=symbol,
                defaults={"name": name, "asset_type": asset_type},
            )

            changed = False
            if asset.name != name:
                asset.name = name
                changed = True
            if asset.asset_type != asset_type:
                asset.asset_type = asset_type
                changed = True
            if changed:
                asset.save(update_fields=["name", "asset_type"])

            assets[symbol] = asset

        return assets

    def _get_demo_user(self):
        User = get_user_model()
        return (
            User.objects.filter(is_superuser=True).order_by("id").first()
            or User.objects.order_by("id").first()
        )

    def _seed_demo_watchlist_and_alerts(self, user, assets):
        WatchlistItem.objects.filter(user=user).delete()
        Alert.objects.filter(user=user).delete()

        add_asset_to_watchlist(
            user,
            assets["BTC/USD"],
            note="Flagship crypto asset for signal monitoring.",
        )
        add_asset_to_watchlist(
            user,
            assets["ETH/USD"],
            note="Watch for elevated momentum and volatility follow-through.",
        )
        add_asset_to_watchlist(
            user,
            assets["XAU/USD"],
            note="Safe-haven monitoring example for reviewer walkthrough.",
        )

        btc_latest = PriceSnapshot.objects.get(asset=assets["BTC/USD"]).price
        eth_latest = PriceSnapshot.objects.get(asset=assets["ETH/USD"]).price
        xau_latest = PriceSnapshot.objects.get(asset=assets["XAU/USD"]).price

        Alert.objects.create(
            user=user,
            asset=assets["BTC/USD"],
            target_price=btc_latest - Decimal("2500"),
            direction="above",
            is_triggered=True,
            is_notified=True,
        )
        Alert.objects.create(
            user=user,
            asset=assets["ETH/USD"],
            target_price=eth_latest + Decimal("150"),
            direction="above",
            is_triggered=False,
            is_notified=False,
        )
        Alert.objects.create(
            user=user,
            asset=assets["XAU/USD"],
            target_price=xau_latest - Decimal("18"),
            direction="below",
            is_triggered=False,
            is_notified=False,
        )

    def _refresh_snapshots(self, assets: Iterable[Asset]):
        snapshot_time = timezone.now()

        for asset in assets:
            latest = PriceOHLC.objects.filter(asset=asset).order_by("-timestamp").first()
            if not latest:
                continue

            PriceSnapshot.objects.update_or_create(
                asset=asset,
                defaults={
                    "timestamp": snapshot_time,
                    "price": latest.close,
                    "open": latest.open,
                    "high": latest.high,
                    "low": latest.low,
                    "close": latest.close,
                    "volume": latest.volume,
                },
            )

    def _build_linear_series(self, *, start, segments):
        """
        Build a deterministic close series from (days, daily_step) segments.
        Returns a list including the starting value.
        """
        values = [float(start)]
        current = float(start)

        for days, step in segments:
            for _ in range(days):
                current += float(step)
                values.append(round(current, 8))

        return values

    def _build_series_from_changes(self, *, start, changes):
        """
        Build a deterministic close series from a sequence of day-over-day changes.
        Returns a list including the starting value.
        """
        values = [float(start)]
        current = float(start)

        for change in changes:
            current += float(change)
            values.append(round(current, 8))

        return values

    def _create_ohlc_series_from_closes(
        self,
        *,
        asset,
        base_time,
        closes,
        range_size,
        base_volume,
        source,
    ):
        """
        Create OHLC rows from a supplied close series using deterministic
        open/high/low/volume rules so screenshots and signal output are stable.
        """
        range_d = Decimal(str(range_size))
        base_volume_d = Decimal(str(base_volume))

        for index, close_value in enumerate(closes):
            timestamp = base_time + timedelta(days=index)
            close_d = Decimal(str(close_value))

            if index == 0:
                previous_close = close_d
            else:
                previous_close = Decimal(str(closes[index - 1]))

            bias = Decimal("0.20") if index % 2 == 0 else Decimal("-0.12")
            open_d = previous_close + (range_d * bias)
            high_d = max(open_d, close_d) + (range_d * Decimal("0.62"))
            low_d = min(open_d, close_d) - (range_d * Decimal("0.68"))

            volume_multiplier = Decimal("1.00") + Decimal(str((index % 5) * 0.04))
            if index >= len(closes) - 5:
                volume_multiplier += Decimal("0.45")

            volume_d = (base_volume_d * volume_multiplier).quantize(Decimal("0.01"))

            PriceOHLC.objects.create(
                asset=asset,
                timestamp=timestamp,
                open=open_d,
                high=high_d,
                low=low_d,
                close=close_d,
                volume=volume_d,
                source=source,
            )