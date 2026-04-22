"""Views for the monitoring homepage, dashboard, and market data endpoints."""

import csv
import logging
from datetime import timedelta
from urllib.parse import unquote

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.dateparse import parse_date
from django.utils.timezone import localtime, now

from ..models import PriceOHLC, PriceSnapshot
from ..services.alerts import get_active_alert_count
from ..services.market import build_dashboard_context, get_freshness_signal
from ..services.signals import get_active_signals
from ..services.watchlist import get_watchlist_count

logger = logging.getLogger(__name__)


def home(request):
    context = {
        "freshness_signal": get_freshness_signal(),
        "watchlist_count": get_watchlist_count(request.user)
        if getattr(request.user, "is_authenticated", False)
        else 0,
        "sidebar_elevated_count": get_active_signals(severity="ELEVATED").count(),
        "active_alerts_count": get_active_alert_count(request.user)
        if getattr(request.user, "is_authenticated", False)
        else 0,
    }
    return render(request, "monitoring/home.html", context)


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
    snapshots = PriceSnapshot.objects.select_related("asset").order_by("-timestamp")[:200]

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

    queryset = PriceOHLC.objects.filter(asset__symbol__iexact=symbol).order_by("timestamp")

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