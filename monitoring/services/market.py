from django.utils.timezone import now

from ..models import Asset, MarketSignal, PriceOHLC, PriceSnapshot
from .alerts import get_active_alert_count
from .signals import get_latest_signals, refresh_signals_for_assets
from .watchlist import get_watchlist_for_user


def get_freshness_signal():
    latest_snapshot = (
        PriceSnapshot.objects
        .select_related("asset")
        .order_by("-timestamp")
        .first()
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


def get_top_mover_summary():
    assets = Asset.objects.all()

    best = None

    for asset in assets:
        rows = list(
            PriceOHLC.objects.filter(asset=asset)
            .order_by("-timestamp")[:4]
        )

        if len(rows) < 4:
            continue

        latest_close = float(rows[0].close)
        base_close = float(rows[-1].close)

        if base_close == 0:
            continue

        pct_move = ((latest_close - base_close) / base_close) * 100.0

        candidate = {
            "symbol": asset.symbol,
            "name": asset.name,
            "pct_move": pct_move,
            "direction": "up" if pct_move >= 0 else "down",
            "abs_move": abs(pct_move),
        }

        if best is None or candidate["abs_move"] > best["abs_move"]:
            best = candidate

    return best


def build_dashboard_context(user, refresh_signals=False):
    assets = list(Asset.objects.order_by("symbol"))
    snapshots = list(
        PriceSnapshot.objects
        .select_related("asset")
        .order_by("-timestamp")[:200]
    )
    ohlc = list(
        PriceOHLC.objects
        .select_related("asset")
        .order_by("-timestamp")[:500]
    )

    if refresh_signals:
        refresh_signals_for_assets(assets)

    latest_signals = get_latest_signals(limit=8)
    elevated_signals_count = get_elevated_signals_count()
    top_mover = get_top_mover_summary()

    return {
        "symbols": [asset.symbol for asset in assets],
        "snapshots": snapshots,
        "ohlc": ohlc,
        "tracked_assets_count": len(assets),
        "active_alerts_count": get_active_alert_count(user),
        "total_alerts": user.alerts.count() if getattr(user, "is_authenticated", False) else 0,
        "recent_snapshots_count": len(snapshots),
        "latest_signals": latest_signals,
        "watchlist_items": get_watchlist_for_user(user, limit=8),
        "freshness_signal": get_freshness_signal(),
        "elevated_signals_count": elevated_signals_count,
        "top_mover": top_mover,
    }