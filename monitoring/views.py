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
from .models import Asset, PriceOHLC, PriceSnapshot
from .services.alerts import (
    create_user_alert_from_form,
    fetch_and_acknowledge_triggered_alerts,
    get_alert_summary,
)
from .services.market import (
    build_dashboard_context,
    get_asset_monitoring_context,
    get_freshness_signal,
    get_top_movers,
)
from .services.signals import (
    get_active_signals,
    refresh_asset_signals,
    refresh_signals_for_assets,
)
from .services.watchlist import (
    add_asset_to_watchlist,
    get_watchlist_count,
    get_watchlist_for_user,
    is_on_watchlist,
    remove_asset_from_watchlist,
)

logger = logging.getLogger(__name__)


def home(request):
    return render(request, "monitoring/home.html")


@login_required
def dashboard(request):
    context = build_dashboard_context(request.user, refresh_signals=True)
    context["sidebar_elevated_count"] = context.get("elevated_signals_count", 0)
    context["watchlist_count"] = context.get(
        "watchlist_count",
        get_watchlist_count(request.user),
    )
    return render(request, "monitoring/dashboard.html", context)


@login_required
def price_data(request):
    snapshots = (
        PriceSnapshot.objects.select_related("asset")
        .order_by("-timestamp")[:200]
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

    snapshots = (
        PriceSnapshot.objects.filter(asset__symbol=symbol, timestamp__gte=cutoff)
        .order_by("timestamp")
    )

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
    alert_summary = get_alert_summary(request.user)

    context = {
        "alerts": alerts,
        "active_alerts_count": alert_summary["active_count"],
        "triggered_alerts_count": alert_summary["triggered_count"],
        "watchlist_count": get_watchlist_count(request.user),
        "sidebar_elevated_count": get_active_signals(severity="ELEVATED").count(),
        "freshness_signal": get_freshness_signal(),
    }
    return render(request, "monitoring/alert_list.html", context)


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
def watchlist_page(request):
    watchlist_items = list(get_watchlist_for_user(request.user))
    alert_summary = get_alert_summary(request.user)

    enriched_rows = []
    for item in watchlist_items:
        latest_snapshot = (
            item.asset.price_snapshots.order_by("-timestamp").first()
        )
        enriched_rows.append(
            {
                "item": item,
                "latest_price": latest_snapshot,
                "pct_move": _get_asset_pct_move(item.asset),
                **_get_asset_badge(item.asset),
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
def signals_page(request):
    assets = list(Asset.objects.order_by("symbol"))
    refresh_signals_for_assets(assets)

    current_severity = request.GET.get("severity", "").upper().strip()
    valid_severities = {"ELEVATED", "WATCHLIST", "INFO"}
    if current_severity not in valid_severities:
        current_severity = ""

    elevated_signals = list(
        get_active_signals(severity="ELEVATED").order_by("-signal_timestamp")
    )
    watchlist_signals = list(
        get_active_signals(severity="WATCHLIST").order_by("-signal_timestamp")
    )
    info_signals = list(
        get_active_signals(severity="INFO").order_by("-signal_timestamp")
    )

    if current_severity == "ELEVATED":
        watchlist_signals = []
        info_signals = []
    elif current_severity == "WATCHLIST":
        elevated_signals = []
        info_signals = []
    elif current_severity == "INFO":
        elevated_signals = []
        watchlist_signals = []

    elevated_count = get_active_signals(severity="ELEVATED").count()
    watchlist_count_signals = get_active_signals(severity="WATCHLIST").count()
    info_count = get_active_signals(severity="INFO").count()
    total_signals_count = elevated_count + watchlist_count_signals + info_count

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


@login_required
def asset_list(request):
    assets = list(Asset.objects.order_by("symbol"))
    top_movers = get_top_movers(limit=50)

    mover_lookup = {row["asset"].id: row for row in top_movers}

    enriched_assets = []
    for asset in assets:
        latest_snapshot = asset.price_snapshots.order_by("-timestamp").first()
        mover_row = mover_lookup.get(asset.id)

        enriched_assets.append(
            {
                "asset": asset,
                "latest_price": latest_snapshot,
                "pct_move": mover_row["pct_move"] if mover_row else _get_asset_pct_move(asset),
                "top_severity": _get_asset_badge(asset)["badge_severity"],
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