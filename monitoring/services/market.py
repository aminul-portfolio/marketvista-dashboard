from django.utils.timezone import now

from ..models import Asset, MarketSignal, PriceOHLC, PriceSnapshot
from .alerts import get_active_alert_count, get_alert_summary
from .signals import (
    get_active_signals,
    get_latest_signals,
    get_signal_history,
    refresh_signals_for_assets,
)
from .watchlist import get_watchlist_count, get_watchlist_for_user, is_on_watchlist


def get_freshness_signal():
    latest_snapshot = (
        PriceSnapshot.objects.select_related("asset").order_by("-timestamp").first()
    )

    if not latest_snapshot:
        return {
            "status": "stale",
            "label": "No market data loaded",
            "delay_minutes": None,
            "last_updated": None,
        }

    delay_minutes = int((now() - latest_snapshot.timestamp).total_seconds() // 60)

    if delay_minutes <= 15:
        status = "fresh"
        label = "Fresh market data"
    elif delay_minutes <= 60:
        status = "delayed"
        label = "Delayed market data"
    else:
        status = "stale"
        label = "Stale market data"

    return {
        "status": status,
        "label": label,
        "delay_minutes": delay_minutes,
        "last_updated": latest_snapshot.timestamp,
    }


def get_elevated_signals_count():
    return MarketSignal.objects.filter(
        is_active=True,
        severity="ELEVATED",
    ).count()


def _get_latest_pct_move(asset):
    rows = list(PriceOHLC.objects.filter(asset=asset).order_by("-timestamp")[:2])

    if len(rows) < 2:
        return None

    latest_close = float(rows[0].close)
    previous_close = float(rows[1].close)

    if previous_close == 0:
        return None

    return ((latest_close - previous_close) / previous_close) * 100.0


def get_top_movers(limit=5):
    movers = []

    for asset in Asset.objects.order_by("symbol"):
        pct_move = _get_latest_pct_move(asset)
        latest_snapshot = (
            PriceSnapshot.objects.filter(asset=asset).order_by("-timestamp").first()
        )

        if pct_move is None or latest_snapshot is None:
            continue

        movers.append(
            {
                "asset": asset,
                "symbol": asset.symbol,
                "name": asset.name,
                "asset_type": asset.asset_type,
                "price": latest_snapshot.price,
                "pct_move": pct_move,
                "direction": "up" if pct_move >= 0 else "down",
                "abs_move": abs(pct_move),
                "signal_count": MarketSignal.objects.filter(
                    asset=asset,
                    is_active=True,
                ).count(),
            }
        )

    movers.sort(key=lambda item: item["abs_move"], reverse=True)
    return movers[:limit]


def get_market_summary(user=None):
    tracked_assets_count = (
        Asset.objects.filter(price_snapshots__isnull=False).distinct().count()
    )
    signals_today_count = MarketSignal.objects.filter(
        signal_timestamp__date=now().date()
    ).count()
    elevated_signals_count = get_elevated_signals_count()
    active_alerts_count = get_active_alert_count(user) if user else 0
    top_movers = get_top_movers(limit=1)
    top_mover = top_movers[0] if top_movers else None

    return {
        "tracked_assets_count": tracked_assets_count,
        "signals_today_count": signals_today_count,
        "elevated_signals_count": elevated_signals_count,
        "active_alerts_count": active_alerts_count,
        "top_mover": top_mover,
    }


def get_asset_monitoring_context(asset, user=None, chart_limit=90):
    latest_snapshot = (
        PriceSnapshot.objects.filter(asset=asset).order_by("-timestamp").first()
    )
    ohlc_rows = list(
        PriceOHLC.objects.filter(asset=asset).order_by("-timestamp")[:chart_limit]
    )
    ohlc_rows.reverse()

    return {
        "asset": asset,
        "latest_snapshot": latest_snapshot,
        "signal_history": get_signal_history(asset, days=30)[:10],
        "active_signals": get_active_signals().filter(asset=asset),
        "ohlc_rows": ohlc_rows,
        "on_watchlist": is_on_watchlist(user, asset) if user else False,
    }


def build_dashboard_context(user, refresh_signals=False):
    assets = list(Asset.objects.order_by("symbol"))

    if refresh_signals:
        refresh_signals_for_assets(assets)

    snapshots = list(
        PriceSnapshot.objects.select_related("asset").order_by("-timestamp")[:200]
    )
    ohlc = list(PriceOHLC.objects.select_related("asset").order_by("-timestamp")[:500])

    alert_summary = get_alert_summary(user)
    market_summary = get_market_summary(user)
    latest_signals = get_latest_signals(limit=8)
    top_movers = get_top_movers(limit=5)

    return {
        "symbols": [asset.symbol for asset in assets],
        "snapshots": snapshots,
        "ohlc": ohlc,
        "tracked_assets_count": market_summary["tracked_assets_count"],
        "active_alerts_count": market_summary["active_alerts_count"],
        "total_alerts": (
            user.alerts.count() if getattr(user, "is_authenticated", False) else 0
        ),
        "recent_snapshots_count": len(snapshots),
        "latest_signals": latest_signals,
        "watchlist_items": get_watchlist_for_user(user, limit=8),
        "watchlist_count": get_watchlist_count(user),
        "freshness_signal": get_freshness_signal(),
        "elevated_signals_count": market_summary["elevated_signals_count"],
        "signals_today_count": market_summary["signals_today_count"],
        "top_mover": market_summary["top_mover"],
        "top_movers": top_movers,
        "triggered_alerts_count": alert_summary["triggered_count"],
        "recent_triggered_alerts": alert_summary["recent_triggered"],
    }