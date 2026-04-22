"""Views for watchlist pages and watchlist actions."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from ..models import Asset, PriceOHLC
from ..services.alerts import get_alert_summary
from ..services.market import get_freshness_signal
from ..services.signals import get_active_signals
from ..services.watchlist import (
    add_asset_to_watchlist,
    get_watchlist_count,
    get_watchlist_for_user,
    remove_asset_from_watchlist,
)


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


@login_required
def watchlist_page(request):
    watchlist_items = list(get_watchlist_for_user(request.user))
    alert_summary = get_alert_summary(request.user)

    enriched_rows = []
    for item in watchlist_items:
        latest_snapshot = item.asset.price_snapshots.order_by("-timestamp").first()
        badge = _get_asset_badge(item.asset)

        enriched_rows.append(
            {
                "item": item,
                "latest_price": latest_snapshot,
                "pct_move": _get_asset_pct_move(item.asset),
                **badge,
            }
        )

    watchlisted_asset_ids = [row["item"].asset_id for row in enriched_rows]
    elevated_on_watchlist = (
        get_active_signals(severity="ELEVATED")
        .filter(asset_id__in=watchlisted_asset_ids)
        .values("asset_id")
        .distinct()
        .count()
    )

    context = {
        "watchlist_items": enriched_rows,
        "total_count": len(enriched_rows),
        "elevated_on_watchlist": elevated_on_watchlist,
        "active_alerts_count": alert_summary["active_count"],
        "freshness_signal": get_freshness_signal(),
        "watchlist_count": get_watchlist_count(request.user),
        "sidebar_elevated_count": get_active_signals(severity="ELEVATED").count(),
    }
    return render(request, "monitoring/watchlist.html", context)


@login_required
def watchlist_add(request, symbol):
    if request.method != "POST":
        return redirect("monitoring:asset_list")

    asset = get_object_or_404(Asset, symbol__iexact=symbol)
    add_asset_to_watchlist(request.user, asset)
    messages.success(request, f"{asset.symbol} added to your watchlist.")

    next_url = (
        request.POST.get("next")
        or request.META.get("HTTP_REFERER")
        or "monitoring:watchlist"
    )
    return redirect(next_url)


@login_required
def watchlist_remove(request, symbol):
    if request.method != "POST":
        return redirect("monitoring:watchlist")

    asset = get_object_or_404(Asset, symbol__iexact=symbol)
    remove_asset_from_watchlist(request.user, asset)
    messages.success(request, f"{asset.symbol} removed from your watchlist.")

    next_url = (
        request.POST.get("next")
        or request.META.get("HTTP_REFERER")
        or "monitoring:watchlist"
    )
    return redirect(next_url)