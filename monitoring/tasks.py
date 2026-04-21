import logging
from datetime import timedelta
from decimal import Decimal, InvalidOperation

import pandas as pd
import requests
import yfinance as yf
from celery import shared_task
from dateutil.parser import parse
from django.conf import settings
from django.utils import timezone

from .models import Asset, PriceOHLC, PriceSnapshot
from .utils import check_alerts_for_asset

logger = logging.getLogger(__name__)

# Provider symbol maps
TWELVE_DATA_SYMBOL_MAP = {
    "BTC/USD": "BTC/USD",
    "ETH/USD": "ETH/USD",
    "XAU/USD": "XAU/USD",
}

YAHOO_SYMBOL_MAP = {
    "BTC/USD": "BTC-USD",
    "ETH/USD": "ETH-USD",
    "XAU/USD": "GC=F",
    "US100": "^NDX",
    "US30": "^DJI",
    "GER40": "^GDAXI",
    "UK100": "^FTSE",
}


def _to_decimal(value, default="0"):
    try:
        return Decimal(str(value if value is not None else default))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


def _normalize_timestamp(ts):
    """
    Ensure timestamps are timezone-aware in the current Django timezone.
    """
    if timezone.is_naive(ts):
        return timezone.make_aware(ts, timezone.get_current_timezone())
    return timezone.localtime(ts, timezone.get_current_timezone())


def _save_ohlc_row(asset, ts, open_price, high_price, low_price, close_price, volume, source):
    """
    Create a PriceOHLC row if it does not already exist.
    """
    if PriceOHLC.objects.filter(asset=asset, timestamp=ts).exists():
        return False

    PriceOHLC.objects.create(
        asset=asset,
        timestamp=ts,
        open=_to_decimal(open_price),
        high=_to_decimal(high_price),
        low=_to_decimal(low_price),
        close=_to_decimal(close_price),
        volume=_to_decimal(volume),
        source=source,
    )
    return True


def _fetch_twelve_data_rows(asset, symbol):
    """
    Fetch recent OHLC rows from Twelve Data and persist them.
    """
    api_key = getattr(settings, "TWELVE_DATA_API_KEY", "")
    if not api_key:
        logger.warning("TWELVE_DATA_API_KEY is not configured; skipping Twelve Data fetch.")
        return 0

    url = "https://api.twelvedata.com/time_series"
    saved_count = 0

    response = requests.get(
        url,
        params={
            "symbol": symbol,
            "interval": "1min",
            "outputsize": 10,
            "apikey": api_key,
        },
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    if data.get("status") == "error" or data.get("code") == 429:
        raise RuntimeError(f"Twelve Data error for {asset.symbol}: {data}")

    for entry in data.get("values", []):
        ts = _normalize_timestamp(parse(entry["datetime"]))
        created = _save_ohlc_row(
            asset=asset,
            ts=ts,
            open_price=entry["open"],
            high_price=entry["high"],
            low_price=entry["low"],
            close_price=entry["close"],
            volume=entry.get("volume", 0),
            source="twelve",
        )
        if created:
            saved_count += 1

    return saved_count


def _fetch_yahoo_rows(asset, yahoo_symbol):
    """
    Fetch recent OHLC rows from Yahoo Finance and persist them.
    """
    end = timezone.now()
    start = end - timedelta(minutes=10)

    df = yf.download(
        yahoo_symbol,
        interval="1m",
        start=start.strftime("%Y-%m-%d %H:%M:%S"),
        end=end.strftime("%Y-%m-%d %H:%M:%S"),
        auto_adjust=False,
        progress=False,
    )

    if df.empty:
        return 0

    saved_count = 0
    for timestamp, row in df.iterrows():
        ts = pd.to_datetime(timestamp, utc=True).tz_convert(
            timezone.get_current_timezone()
        ).to_pydatetime()

        created = _save_ohlc_row(
            asset=asset,
            ts=ts,
            open_price=row.get("Open"),
            high_price=row.get("High"),
            low_price=row.get("Low"),
            close_price=row.get("Close"),
            volume=row.get("Volume", 0),
            source="yahoo",
        )
        if created:
            saved_count += 1

    return saved_count


@shared_task
def fetch_and_store_ohlc():
    """
    Background task: fetch and persist recent OHLC rows for all mapped assets.
    """
    logger.info("Starting OHLC fetch task...")
    total_saved = 0

    for symbol, yahoo_symbol in YAHOO_SYMBOL_MAP.items():
        asset = Asset.objects.filter(symbol=symbol).first()
        if not asset:
            logger.warning("No asset found for symbol %s", symbol)
            continue

        success = False

        if symbol in TWELVE_DATA_SYMBOL_MAP:
            try:
                saved = _fetch_twelve_data_rows(asset, TWELVE_DATA_SYMBOL_MAP[symbol])
                total_saved += saved
                logger.info("Saved %s OHLC rows from Twelve Data for %s", saved, symbol)
                success = True
            except Exception:
                logger.exception("Twelve Data fetch failed for %s", symbol)

        if not success:
            try:
                saved = _fetch_yahoo_rows(asset, yahoo_symbol)
                total_saved += saved
                logger.info("Saved %s OHLC rows from Yahoo Finance for %s", saved, symbol)
            except Exception:
                logger.exception("Yahoo fallback failed for %s", symbol)

    logger.info("OHLC fetch task complete. Total rows saved: %s", total_saved)
    return total_saved


@shared_task
def fetch_snapshot_prices():
    """
    Background task: fetch current snapshot prices for all assets, persist them,
    and check alert triggers.
    """
    logger.info("Starting snapshot fetch task...")
    total_saved = 0
    total_triggered = 0

    for asset in Asset.objects.all():
        yahoo_symbol = YAHOO_SYMBOL_MAP.get(asset.symbol)
        if not yahoo_symbol:
            logger.warning("No Yahoo mapping configured for %s", asset.symbol)
            continue

        try:
            ticker = yf.Ticker(yahoo_symbol)
            data = ticker.history(period="1d", interval="1m")

            if data.empty:
                logger.warning("No snapshot data returned for %s", asset.symbol)
                continue

            latest = data.iloc[-1]
            ts = pd.to_datetime(latest.name, utc=True).tz_convert(
                timezone.get_current_timezone()
            ).to_pydatetime()

            snapshot, created = PriceSnapshot.objects.get_or_create(
                asset=asset,
                timestamp=ts,
                defaults={
                    "price": _to_decimal(latest.get("Close")),
                    "open": _to_decimal(latest.get("Open")),
                    "high": _to_decimal(latest.get("High")),
                    "low": _to_decimal(latest.get("Low")),
                    "close": _to_decimal(latest.get("Close")),
                    "volume": _to_decimal(latest.get("Volume", 0)),
                },
            )

            if created:
                total_saved += 1

            latest_price = latest.get("Close")
            triggered = check_alerts_for_asset(asset, latest_price)
            total_triggered += triggered

            logger.info(
                "Snapshot processed for %s at %s | created=%s | alerts_triggered=%s",
                asset.symbol,
                ts,
                created,
                triggered,
            )

        except Exception:
            logger.exception("Snapshot fetch failed for %s", asset.symbol)

    logger.info(
        "Snapshot fetch task complete. Snapshots saved: %s | Alerts triggered: %s",
        total_saved,
        total_triggered,
    )
    return {
        "snapshots_saved": total_saved,
        "alerts_triggered": total_triggered,
    }