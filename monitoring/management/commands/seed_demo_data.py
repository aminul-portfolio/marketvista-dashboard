from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from monitoring.models import Asset, MarketSignal, PriceOHLC, PriceSnapshot
from monitoring.services.signals import refresh_signals_for_assets
from monitoring.services.watchlist import add_asset_to_watchlist


class Command(BaseCommand):
    help = "Seed MarketVista with reviewer-ready demo data."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Resetting MarketVista demo data..."))

        # Clear signal + price data only
        MarketSignal.objects.all().delete()
        PriceSnapshot.objects.all().delete()
        PriceOHLC.objects.all().delete()

        # Keep existing assets if present, otherwise create them
        btc, _ = Asset.objects.get_or_create(
            symbol="BTC/USD",
            defaults={"name": "Bitcoin", "asset_type": "crypto"},
        )
        eth, _ = Asset.objects.get_or_create(
            symbol="ETH/USD",
            defaults={"name": "Ethereum", "asset_type": "crypto"},
        )

        base_time = timezone.now() - timedelta(days=25)

        btc_prices = [
            90000, 90200, 90150, 90300, 90400,
            90500, 90650, 90700, 90800, 91000,
            91200, 91350, 91500, 91700, 91900,
            92050, 92200, 92500, 92800, 93200,
            93600, 94100, 94700, 95400, 96200,
        ]

        eth_prices = [
            3200, 3210, 3190, 3225, 3215,
            3250, 3275, 3260, 3300, 3340,
            3310, 3360, 3390, 3375, 3420,
            3450, 3440, 3490, 3550, 3520,
            3600, 3680, 3620, 3750, 3890,
        ]

        self._create_ohlc_series(
            asset=btc,
            base_time=base_time,
            prices=btc_prices,
            open_offset=Decimal("100"),
            high_offset=Decimal("150"),
            low_offset=Decimal("180"),
            base_volume=Decimal("1000"),
            volume_step=Decimal("10"),
        )

        self._create_ohlc_series(
            asset=eth,
            base_time=base_time,
            prices=eth_prices,
            open_offset=Decimal("20"),
            high_offset=Decimal("35"),
            low_offset=Decimal("40"),
            base_volume=Decimal("800"),
            volume_step=Decimal("12"),
        )

        # Fresh snapshots for dashboard/demo readiness
        for asset in Asset.objects.all():
            latest = PriceOHLC.objects.filter(asset=asset).order_by("-timestamp").first()
            if latest:
                PriceSnapshot.objects.update_or_create(
                    asset=asset,
                    defaults={
                        "timestamp": timezone.now(),
                        "price": latest.close,
                        "open": latest.open,
                        "high": latest.high,
                        "low": latest.low,
                        "close": latest.close,
                        "volume": latest.volume,
                    },
                )

        refresh_signals_for_assets()

        # Optional reviewer watchlist
        User = get_user_model()
        demo_user = User.objects.filter(is_superuser=True).order_by("id").first()

        if demo_user:
            add_asset_to_watchlist(
                demo_user,
                btc,
                note="Flagship crypto asset for signal monitoring.",
            )
            add_asset_to_watchlist(
                demo_user,
                eth,
                note="Watch for elevated momentum and volatility follow-through.",
            )

        self.stdout.write(self.style.SUCCESS("MarketVista demo data seeded successfully."))
        self.stdout.write(f"Assets: {Asset.objects.count()}")
        self.stdout.write(f"OHLC rows: {PriceOHLC.objects.count()}")
        self.stdout.write(f"Snapshots: {PriceSnapshot.objects.count()}")
        self.stdout.write(f"Signals: {MarketSignal.objects.count()}")

    def _create_ohlc_series(
        self,
        *,
        asset,
        base_time,
        prices,
        open_offset,
        high_offset,
        low_offset,
        base_volume,
        volume_step,
    ):
        for i, close_price in enumerate(prices):
            ts = base_time + timedelta(days=i)
            close_d = Decimal(str(close_price))
            open_d = close_d - open_offset
            high_d = close_d + high_offset
            low_d = close_d - low_offset
            volume_d = base_volume + (volume_step * i)

            PriceOHLC.objects.create(
                asset=asset,
                timestamp=ts,
                open=open_d,
                high=high_d,
                low=low_d,
                close=close_d,
                volume=volume_d,
                source="demo_seed",
            )