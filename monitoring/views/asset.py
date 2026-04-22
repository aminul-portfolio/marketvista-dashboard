"""Views for asset browsing and asset detail pages."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from ..models import Asset, PriceOHLC
from ..services.market import (
    get_asset_monitoring_context,
    get_freshness_signal,
    get_top_movers,
)
from ..services.signals import get_active_signals, refresh_asset_signals
from ..services.watchlist import get_watchlist_count, is_on_watchlist


def _get_asset_pct_move(asset, periods=4):
    rows = list(
        PriceOHLC.objects.filter(asset=asset)
        .order_by("-timestamp")[:periods]
    )
    if len(rows) < periods:
        return None

    latest_close = float(rows[0].close)
    base_close = float(rows[-1].close)

    if base_close == 0:
        return None

    return ((latest_close - base_close) / base_close) * 100.0


def _get_asset_badge(asset):
    active_signals = get_active_signals().filter(asset=asset)

    elevated_count = active_signals.filter(severity="ELEVATED").count()
    watchlist_count = active_signals.filter(severity="WATCHLIST").count()
    info_count = active_signals.filter(severity="INFO").count()

    if elevated_count > 0:
        return {
            "badge_text": f"{elevated_count} elevated",
            "badge_color": "#f97316",
            "badge_severity": "elevated",
        }

    if watchlist_count > 0:
        return {
            "badge_text": f"{watchlist_count} watchlist",
            "badge_color": "#f59e0b",
            "badge_severity": "watchlist",
        }

    if info_count > 0:
        return {
            "badge_text": f"{info_count} info",
            "badge_color": "rgba(255,255,255,0.28)",
            "badge_severity": "info",
        }

    return {
        "badge_text": "no signals",
        "badge_color": "rgba(255,255,255,0.12)",
        "badge_severity": "none",
    }


def _build_asset_chart_points(ohlc_rows):
    if not ohlc_rows:
        return []

    closes = [float(row.close) for row in ohlc_rows]
    min_close = min(closes)
    max_close = max(closes)

    points = []
    for index, row in enumerate(ohlc_rows):
        close_value = float(row.close)

        if max_close == min_close:
            height_pct = 65
        else:
            normalized = (close_value - min_close) / (max_close - min_close)
            height_pct = 28 + (normalized * 72)

        points.append(
            {
                "height_pct": round(height_pct, 2),
                "tooltip": f"{row.timestamp:%d %b %Y} · ${close_value:,.2f}",
                "is_latest": index == len(ohlc_rows) - 1,
            }
        )

    return points


@login_required
def asset_list(request):
    assets = list(Asset.objects.order_by("symbol"))
    top_movers = get_top_movers(limit=50)

    mover_lookup = {row["asset"].id: row for row in top_movers}

    enriched_assets = []
    for asset in assets:
        latest_snapshot = asset.price_snapshots.order_by("-timestamp").first()
        mover_row = mover_lookup.get(asset.id)
        badge = _get_asset_badge(asset)

        enriched_assets.append(
            {
                "asset": asset,
                "latest_price": latest_snapshot,
                "pct_move": mover_row["pct_move"] if mover_row else _get_asset_pct_move(asset),
                "top_severity": badge["badge_severity"],
                "badge_text": badge["badge_text"],
                "badge_color": badge["badge_color"],
                "on_watchlist": is_on_watchlist(request.user, asset),
            }
        )

    context = {
        "assets": enriched_assets,
        "freshness_signal": get_freshness_signal(),
        "sidebar_elevated_count": get_active_signals(severity="ELEVATED").count(),
        "watchlist_count": get_watchlist_count(request.user),
    }
    return render(request, "monitoring/asset_list.html", context)


@login_required
def asset_detail(request, symbol):
    asset = get_object_or_404(Asset, symbol__iexact=symbol)
    refresh_asset_signals(asset)

    period = request.GET.get("period", "7d")
    period_days = {"7d": 7, "30d": 30, "90d": 90}.get(period, 7)

    monitoring_context = get_asset_monitoring_context(
        asset,
        user=request.user,
        chart_limit=90,
    )

    ohlc_rows = monitoring_context["ohlc_rows"][-period_days:]
    chart_points = _build_asset_chart_points(ohlc_rows)

    chart_start_label = ohlc_rows[0].timestamp.strftime("%d %b") if ohlc_rows else ""
    chart_end_label = ohlc_rows[-1].timestamp.strftime("%d %b") if ohlc_rows else ""

    active_signals = monitoring_context["active_signals"]
    signal_history = monitoring_context["signal_history"][:10]
    latest_snapshot = monitoring_context["latest_snapshot"]
    on_watchlist = monitoring_context["on_watchlist"]

    asset_alerts = request.user.alerts.filter(asset=asset).order_by("-created_at")

    context = {
        "asset": asset,
        "latest_snapshot": latest_snapshot,
        "pct_move": _get_asset_pct_move(asset),
        "ohlc_rows": ohlc_rows,
        "chart_points": chart_points,
        "chart_start_label": chart_start_label,
        "chart_end_label": chart_end_label,
        "signal_history": signal_history,
        "asset_alerts": asset_alerts,
        "on_watchlist": on_watchlist,
        "has_elevated_signal": active_signals.filter(severity="ELEVATED").exists(),
        "period": period,
        "freshness_signal": get_freshness_signal(),
        "sidebar_elevated_count": get_active_signals(severity="ELEVATED").count(),
        "watchlist_count": get_watchlist_count(request.user),
    }
    return render(request, "monitoring/asset_detail.html", context)