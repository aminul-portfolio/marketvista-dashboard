import csv
import logging
from datetime import timedelta
from urllib.parse import unquote

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.utils.timezone import localtime, now

from .forms import AlertForm
from .models import Asset, MarketSignal, PriceOHLC, PriceSnapshot, WatchlistItem
from .services.alerts import (
    create_user_alert_from_form,
    fetch_and_acknowledge_triggered_alerts,
)
from .services.market import build_dashboard_context, get_freshness_signal
from .services.signals import refresh_signals_for_assets
from .services.watchlist import (
    add_asset_to_watchlist,
    get_watchlist_for_user,
    remove_asset_from_watchlist,
)

logger = logging.getLogger(__name__)


def home(request):
    return render(request, "monitoring/home.html")


@login_required
def dashboard(request):
    context = build_dashboard_context(request.user, refresh_signals=True)
    return render(request, "monitoring/dashboard.html", context)


@login_required
def price_data(request):
    snapshots = (
        PriceSnapshot.objects.select_related("asset").order_by("-timestamp")[:200]
    )
    data = [
        {
            "symbol": snapshot.asset.symbol,
            "price": round(float(snapshot.price), 2),
            "timestamp": localtime(snapshot.timestamp).strftime("%Y-%m-%d %H:%M:%S"),
        }
        for snapshot in snapshots
    ]
    return JsonResponse({"snapshots": data})


@login_required
def ohlc_data(request):
    symbol = unquote(request.GET.get("symbol", "").strip())
    start_date = request.GET.get("start", "").strip()
    end_date = request.GET.get("end", "").strip()

    if not symbol:
        return JsonResponse({"error": "Missing symbol"}, status=400)

    queryset = PriceOHLC.objects.filter(asset__symbol__iexact=symbol).order_by(
        "timestamp"
    )

    parsed_start = parse_date(start_date) if start_date else None
    parsed_end = parse_date(end_date) if end_date else None

    if parsed_start:
        queryset = queryset.filter(timestamp__date__gte=parsed_start)
    if parsed_end:
        queryset = queryset.filter(timestamp__date__lte=parsed_end)

    rows = list(queryset[:300])

    if not rows:
        logger.warning("No OHLC data found for symbol: %s", symbol)
        return JsonResponse(
            {
                "ohlc": [],
                "last_updated": None,
                "server_time": now().isoformat(),
                "delay_minutes": None,
            }
        )

    latest_ts = rows[-1].timestamp
    delay_minutes = int((now() - latest_ts).total_seconds() // 60)

    data = [
        {
            "timestamp": row.timestamp.isoformat(),
            "open": float(row.open),
            "high": float(row.high),
            "low": float(row.low),
            "close": float(row.close),
            "volume": float(row.volume or 0),
        }
        for row in rows
    ]

    return JsonResponse(
        {
            "ohlc": data,
            "last_updated": latest_ts.isoformat(),
            "server_time": now().isoformat(),
            "delay_minutes": delay_minutes,
        }
    )


@login_required
def line_price_data(request):
    symbol = request.GET.get("symbol")
    range_str = request.GET.get("range", "30m")

    if not symbol:
        return JsonResponse({"data": []})

    delta_map = {
        "30m": timedelta(minutes=30),
        "1h": timedelta(hours=1),
        "24h": timedelta(hours=24),
    }
    delta = delta_map.get(range_str, timedelta(minutes=30))
    cutoff = now() - delta

    snapshots = PriceSnapshot.objects.filter(
        asset__symbol=symbol,
        timestamp__gte=cutoff,
    ).order_by("timestamp")

    data = [
        {"timestamp": item.timestamp.isoformat(), "price": float(item.price)}
        for item in snapshots
    ]
    return JsonResponse({"data": data})


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("monitoring:dashboard")
    else:
        form = UserCreationForm()
    return render(request, "monitoring/register.html", {"form": form})


@login_required
def create_alert(request):
    if request.method == "POST":
        form = AlertForm(request.POST)
        if form.is_valid():
            create_user_alert_from_form(request.user, form)
            return redirect("monitoring:alert_list")
    else:
        form = AlertForm()
    return render(request, "monitoring/create_alert.html", {"form": form})


@login_required
def alert_list(request):
    alerts = request.user.alerts.select_related("asset").all()
    return render(request, "monitoring/alert_list.html", {"alerts": alerts})


@login_required
def export_prices_csv(request):
    snapshots = PriceSnapshot.objects.select_related("asset").order_by("-timestamp")

    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="price_snapshots.csv"'},
    )

    writer = csv.writer(response)
    writer.writerow(["Symbol", "Price", "Timestamp"])

    for snapshot in snapshots:
        writer.writerow(
            [
                snapshot.asset.symbol,
                snapshot.price,
                snapshot.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            ]
        )

    return response


@login_required
def triggered_alerts_api(request):
    try:
        triggered = fetch_and_acknowledge_triggered_alerts(request.user)
        return JsonResponse({"alerts": triggered})
    except Exception as exc:
        logger.exception("Error in triggered_alerts_api")
        return JsonResponse({"error": str(exc)}, status=500)


def _get_asset_pct_move(asset, periods=4):
    """Return 3-period percentage move from PriceOHLC. Returns None if insufficient data."""
    rows = list(PriceOHLC.objects.filter(asset=asset).order_by("-timestamp")[:periods])
    if len(rows) < periods:
        return None
    latest_close = float(rows[0].close)
    base_close = float(rows[-1].close)
    if base_close == 0:
        return None
    return ((latest_close - base_close) / base_close) * 100.0


def _get_top_severity(asset):
    """Return the highest active signal severity for an asset, or None."""
    if MarketSignal.objects.filter(
        asset=asset,
        is_active=True,
        severity="ELEVATED",
    ).exists():
        return "ELEVATED"
    if MarketSignal.objects.filter(
        asset=asset,
        is_active=True,
        severity="WATCHLIST",
    ).exists():
        return "WATCHLIST"
    if MarketSignal.objects.filter(
        asset=asset,
        is_active=True,
        severity="INFO",
    ).exists():
        return "INFO"
    return None


def _severity_badge(asset):
    """Return badge text and color for signal severity on a watchlist row."""
    elevated = MarketSignal.objects.filter(
        asset=asset,
        is_active=True,
        severity="ELEVATED",
    ).count()
    watchlist = MarketSignal.objects.filter(
        asset=asset,
        is_active=True,
        severity="WATCHLIST",
    ).count()
    info = MarketSignal.objects.filter(
        asset=asset,
        is_active=True,
        severity="INFO",
    ).count()

    if elevated > 0:
        return {
            "badge_text": f"{elevated} elevated",
            "badge_color": "#f97316",
            "badge_severity": "elevated",
        }
    if watchlist > 0:
        return {
            "badge_text": f"{watchlist} watchlist",
            "badge_color": "#f59e0b",
            "badge_severity": "watchlist",
        }
    if info > 0:
        return {
            "badge_text": f"{info} info",
            "badge_color": "rgba(255,255,255,0.2)",
            "badge_severity": "info",
        }
    return {
        "badge_text": "no signals",
        "badge_color": "rgba(255,255,255,0.1)",
        "badge_severity": "none",
    }


@login_required
def watchlist_page(request):
    """Full watchlist page with enriched per-asset data."""
    watchlist_qs = (
        WatchlistItem.objects.filter(user=request.user)
        .select_related("asset")
        .order_by("asset__symbol")
    )

    enriched = []
    for item in watchlist_qs:
        latest_snapshot = (
            PriceSnapshot.objects.filter(asset=item.asset).order_by("-timestamp").first()
        )
        badge = _severity_badge(item.asset)
        enriched.append(
            {
                "item": item,
                "latest_price": latest_snapshot,
                "pct_move": _get_asset_pct_move(item.asset),
                **badge,
            }
        )

    watchlisted_asset_ids = [row["item"].asset_id for row in enriched]
    elevated_on_watchlist = (
        MarketSignal.objects.filter(
            asset_id__in=watchlisted_asset_ids,
            is_active=True,
            severity="ELEVATED",
        )
        .values("asset_id")
        .distinct()
        .count()
    )

    context = {
        "watchlist_items": enriched,
        "total_count": len(enriched),
        "elevated_on_watchlist": elevated_on_watchlist,
        "active_alerts_count": request.user.alerts.filter(is_triggered=False).count(),
        "freshness_signal": get_freshness_signal(),
        "watchlist_count": len(enriched),
        "sidebar_elevated_count": MarketSignal.objects.filter(
            is_active=True,
            severity="ELEVATED",
        ).count(),
    }
    return render(request, "monitoring/watchlist.html", context)


@login_required
def signals_page(request):
    """Signals page grouped by severity with optional ?severity= filter."""
    assets = list(Asset.objects.all())
    refresh_signals_for_assets(assets)

    current_severity = request.GET.get("severity", "").upper().strip()
    valid_severities = {"ELEVATED", "WATCHLIST", "INFO"}
    if current_severity not in valid_severities:
        current_severity = ""

    base_qs = MarketSignal.objects.filter(is_active=True).select_related("asset")

    if current_severity:
        elevated_signals = (
            list(base_qs.filter(severity="ELEVATED").order_by("-signal_timestamp"))
            if current_severity == "ELEVATED"
            else []
        )
        watchlist_signals = (
            list(base_qs.filter(severity="WATCHLIST").order_by("-signal_timestamp"))
            if current_severity == "WATCHLIST"
            else []
        )
        info_signals = (
            list(base_qs.filter(severity="INFO").order_by("-signal_timestamp"))
            if current_severity == "INFO"
            else []
        )
    else:
        elevated_signals = list(
            base_qs.filter(severity="ELEVATED").order_by("-signal_timestamp")
        )
        watchlist_signals = list(
            base_qs.filter(severity="WATCHLIST").order_by("-signal_timestamp")
        )
        info_signals = list(base_qs.filter(severity="INFO").order_by("-signal_timestamp"))

    elevated_count = base_qs.filter(severity="ELEVATED").count()
    watchlist_count = base_qs.filter(severity="WATCHLIST").count()
    info_count = base_qs.filter(severity="INFO").count()
    total_signals_count = elevated_count + watchlist_count + info_count

    context = {
        "elevated_signals": elevated_signals,
        "watchlist_signals": watchlist_signals,
        "info_signals": info_signals,
        "elevated_count": elevated_count,
        "watchlist_count": watchlist_count,
        "info_count": info_count,
        "total_signals_count": total_signals_count,
        "current_severity": current_severity,
        "freshness_signal": get_freshness_signal(),
        "sidebar_elevated_count": elevated_count,
        "watchlist_count_sidebar": (
            WatchlistItem.objects.filter(user=request.user).count()
            if request.user.is_authenticated
            else 0
        ),
    }
    return render(request, "monitoring/signals.html", context)


@login_required
def asset_list(request):
    """Browse all tracked assets with latest prices and signal status."""
    assets = list(Asset.objects.order_by("symbol"))

    watchlisted_ids = set(
        WatchlistItem.objects.filter(user=request.user).values_list("asset_id", flat=True)
    )

    enriched = []
    for asset in assets:
        latest_snapshot = (
            PriceSnapshot.objects.filter(asset=asset).order_by("-timestamp").first()
        )
        enriched.append(
            {
                "asset": asset,
                "latest_price": latest_snapshot,
                "pct_move": _get_asset_pct_move(asset),
                "top_severity": _get_top_severity(asset),
                "on_watchlist": asset.id in watchlisted_ids,
            }
        )

    context = {
        "assets": enriched,
        "freshness_signal": get_freshness_signal(),
        "sidebar_elevated_count": MarketSignal.objects.filter(
            is_active=True,
            severity="ELEVATED",
        ).count(),
        "watchlist_count": len(watchlisted_ids),
    }
    return render(request, "monitoring/asset_list.html", context)


@login_required
def asset_detail(request, symbol):
    """Asset detail page — signal history, alerts, price chart, RiskWise CTA."""
    asset = get_object_or_404(Asset, symbol__iexact=symbol)

    from .services.signals import refresh_asset_signals

    refresh_asset_signals(asset)

    period = request.GET.get("period", "7d")
    period_days = {"7d": 7, "30d": 30, "90d": 90}.get(period, 7)

    ohlc_rows = list(
        PriceOHLC.objects.filter(asset=asset).order_by("-timestamp")[:period_days]
    )
    ohlc_rows.reverse()

    latest_snapshot = (
        PriceSnapshot.objects.filter(asset=asset).order_by("-timestamp").first()
    )

    pct_move = _get_asset_pct_move(asset)

    signal_history = (
        MarketSignal.objects.filter(asset=asset).order_by("-signal_timestamp")[:10]
    )

    asset_alerts = (
        request.user.alerts.filter(asset=asset).order_by("-created_at")
        if request.user.is_authenticated
        else []
    )

    on_watchlist = WatchlistItem.objects.filter(
        user=request.user,
        asset=asset,
    ).exists()

    has_elevated_signal = MarketSignal.objects.filter(
        asset=asset,
        is_active=True,
        severity="ELEVATED",
    ).exists()

    context = {
        "asset": asset,
        "latest_snapshot": latest_snapshot,
        "pct_move": pct_move,
        "ohlc_rows": ohlc_rows,
        "signal_history": signal_history,
        "asset_alerts": asset_alerts,
        "on_watchlist": on_watchlist,
        "has_elevated_signal": has_elevated_signal,
        "period": period,
        "freshness_signal": get_freshness_signal(),
        "sidebar_elevated_count": MarketSignal.objects.filter(
            is_active=True,
            severity="ELEVATED",
        ).count(),
        "watchlist_count": WatchlistItem.objects.filter(user=request.user).count(),
    }
    return render(request, "monitoring/asset_detail.html", context)


@login_required
def watchlist_add(request, symbol):
    """POST — add asset to watchlist."""
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
    """POST — remove asset from watchlist."""
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