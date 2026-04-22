"""Views for signal browsing and signal-related monitoring pages."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ..models import Asset
from ..services.market import get_freshness_signal
from ..services.signals import get_active_signals, refresh_signals_for_assets
from ..services.watchlist import get_watchlist_count


@login_required
def signals_page(request):
    assets = list(Asset.objects.order_by("symbol"))
    refresh_signals_for_assets(assets)

    current_severity = request.GET.get("severity", "").upper().strip()
    valid_severities = {"ELEVATED", "WATCHLIST", "INFO"}
    if current_severity not in valid_severities:
        current_severity = ""

    elevated_qs = get_active_signals(severity="ELEVATED").order_by("-signal_timestamp")
    watchlist_qs = get_active_signals(severity="WATCHLIST").order_by("-signal_timestamp")
    info_qs = get_active_signals(severity="INFO").order_by("-signal_timestamp")

    elevated_count = elevated_qs.count()
    watchlist_count_signals = watchlist_qs.count()
    info_count = info_qs.count()
    total_signals_count = elevated_count + watchlist_count_signals + info_count

    elevated_signals = list(elevated_qs)
    watchlist_signals = list(watchlist_qs)
    info_signals = list(info_qs)

    if current_severity == "ELEVATED":
        watchlist_signals = []
        info_signals = []
    elif current_severity == "WATCHLIST":
        elevated_signals = []
        info_signals = []
    elif current_severity == "INFO":
        elevated_signals = []
        watchlist_signals = []

    context = {
        "elevated_signals": elevated_signals,
        "watchlist_signals": watchlist_signals,
        "info_signals": info_signals,
        "elevated_count": elevated_count,
        "watchlist_count_signals": watchlist_count_signals,
        "info_count": info_count,
        "total_signals_count": total_signals_count,
        "current_severity": current_severity,
        "freshness_signal": get_freshness_signal(),
        "sidebar_elevated_count": elevated_count,
        "watchlist_count": get_watchlist_count(request.user),
    }
    return render(request, "monitoring/signals.html", context)