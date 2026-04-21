from celery import shared_task
from .models import Asset, PriceOHLC, PriceSnapshot
from django.conf import settings
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from dateutil.parser import parse
import pandas as pd
import yfinance as yf
from .utils import check_alerts_for_asset
import requests
import logging

logger = logging.getLogger(__name__)

# 🔁 Separate mapping for each data provider
twelve_map = {
    "BTC/USD": "BTC/USD",
    "ETH/USD": "ETH/USD",
    "XAU/USD": "XAU/USD",  # May fail, depending on TwelveData support
}

yahoo_map = {
    "BTC/USD": "BTC-USD",
    "ETH/USD": "ETH-USD",
    "XAU/USD": "GC=F",
    "US100": "^NDX",
    "US30": "^DJI",
    "GER40": "^GDAXI",
    "UK100": "^FTSE",
}

@shared_task
def fetch_and_store_ohlc():
    logger.info("📊 Starting OHLC fetch task...")

    twelve_url = "https://api.twelvedata.com/time_series"
    api_key = settings.TWELVE_DATA_API_KEY
    interval = "1min"

    for symbol, yahoo_symbol in yahoo_map.items():
        asset = Asset.objects.filter(symbol=symbol).first()
        if not asset:
            logger.warning(f"⚠️ No asset found for {symbol}")
            continue

        success = False

        # 🟢 Try Twelve Data only if supported
        if symbol in twelve_map:
            try:
                response = requests.get(twelve_url, params={
                    "symbol": twelve_map[symbol],
                    "interval": interval,
                    "outputsize": 10,
                    "apikey": api_key
                }, timeout=10)

                data = response.json()

                if data.get("status") == "error" or data.get("code") == 429:
                    logger.warning(f"❌ API error for {symbol}: {data}")
                    raise Exception("Twelve Data limit reached or failed")

                if "values" in data:
                    for entry in data["values"]:
                        ts = parse(entry["datetime"])
                        if timezone.is_naive(ts):
                            ts = timezone.make_aware(ts, timezone.get_current_timezone())

                        if PriceOHLC.objects.filter(asset=asset, timestamp=ts).exists():
                            continue

                        PriceOHLC.objects.create(
                            asset=asset,
                            timestamp=ts,
                            open=Decimal(entry["open"]),
                            high=Decimal(entry["high"]),
                            low=Decimal(entry["low"]),
                            close=Decimal(entry["close"]),
                            volume=Decimal(entry.get("volume", 0)),
                            source='twelve'
                        )
                    logger.info(f"🟢 OHLC saved from Twelve Data for {symbol}")
                    success = True

            except Exception as e:
                logger.error(f"❌ Twelve Data failed for {symbol}: {e}")

        # 🔁 Yahoo fallback
        if not success:
            try:
                end = datetime.utcnow()
                start = end - timedelta(minutes=10)

                df = yf.download(
                    yahoo_symbol,
                    interval="1m",
                    start=start.strftime('%Y-%m-%d %H:%M:%S'),
                    end=end.strftime('%Y-%m-%d %H:%M:%S'),
                    auto_adjust=False,
                    progress=False
                )

                for timestamp, row in df.iterrows():
                    ts = pd.to_datetime(timestamp, utc=True).tz_convert(timezone.get_current_timezone()).to_pydatetime()

                    if PriceOHLC.objects.filter(asset=asset, timestamp=ts).exists():
                        continue

                    PriceOHLC.objects.create(
                        asset=asset,
                        timestamp=ts,
                        open=Decimal(row["Open"]),
                        high=Decimal(row["High"]),
                        low=Decimal(row["Low"]),
                        close=Decimal(row["Close"]),
                        volume=Decimal(row.get("Volume", 0)),
                        source='yahoo'
                    )

                logger.info(f"🔵 OHLC saved from Yahoo Finance for {symbol}")

            except Exception as e:
                logger.error(f"❌ Yahoo fallback failed for {symbol}: {e}")


@shared_task
def fetch_snapshot_prices():
    logger.info("📈 Starting snapshot fetch task...")

    for asset in Asset.objects.all():
        yf_symbol = yahoo_map.get(asset.symbol)
        if not yf_symbol:
            logger.warning(f"❌ No Yahoo mapping for {asset.symbol}")
            continue

        try:
            ticker = yf.Ticker(yf_symbol)
            data = ticker.history(period="1d", interval="1m")

            if not data.empty:
                latest = data.iloc[-1]
                ts = pd.to_datetime(latest.name, utc=True).tz_convert(timezone.get_current_timezone()).to_pydatetime()

                PriceSnapshot.objects.get_or_create(
                    asset=asset,
                    timestamp=ts,
                    defaults={
                        "price": Decimal(latest["Close"]),
                        "open": Decimal(latest["Open"]),
                        "high": Decimal(latest["High"]),
                        "low": Decimal(latest["Low"]),
                        "close": Decimal(latest["Close"]),
                        "volume": Decimal(latest.get("Volume", 0))
                    }
                )

                # ✅ ✅ ✅ Trigger alert check
                check_alerts_for_asset(asset, latest["Close"])

                logger.info(f"✅ Snapshot + Alert Check complete for {asset.symbol} at {ts}")

        except Exception as e:
            logger.error(f"❌ Snapshot fetch failed for {asset.symbol}: {e}")

