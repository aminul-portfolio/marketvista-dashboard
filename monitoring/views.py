import csv
import io
import logging
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from urllib.parse import unquote
from django.utils.dateparse import parse_date
import pandas as pd

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.timezone import localtime, now
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import AlertForm, TradeForm, UnifiedRiskForm
from .models import PriceOHLC, PriceSnapshot, Trade
from .services.alerts import (
    create_user_alert_from_form,
    fetch_and_acknowledge_triggered_alerts,
)
from .services.market import build_dashboard_context

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
        PriceSnapshot.objects
        .select_related("asset")
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

    queryset = (
        PriceOHLC.objects
        .filter(asset__symbol__iexact=symbol)
        .order_by("timestamp")
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
        PriceSnapshot.objects
        .filter(asset__symbol=symbol, timestamp__gte=cutoff)
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


class TradeListView(LoginRequiredMixin, ListView):
    model = Trade
    template_name = "monitoring/trade_list.html"
    context_object_name = "trades"

    def get_queryset(self):
        return Trade.objects.filter(user=self.request.user).order_by("-opened_at")


class TradeCreateView(LoginRequiredMixin, CreateView):
    model = Trade
    form_class = TradeForm
    template_name = "monitoring/trade_form.html"
    success_url = reverse_lazy("monitoring:trade_list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class TradeUpdateView(LoginRequiredMixin, UpdateView):
    model = Trade
    form_class = TradeForm
    template_name = "monitoring/trade_form.html"
    success_url = reverse_lazy("monitoring:trade_list")

    def get_queryset(self):
        return Trade.objects.filter(user=self.request.user)


class TradeDeleteView(LoginRequiredMixin, DeleteView):
    model = Trade
    template_name = "monitoring/trade_confirm_delete.html"
    success_url = reverse_lazy("monitoring:trade_list")

    def get_queryset(self):
        return Trade.objects.filter(user=self.request.user)


class TradeDetailView(LoginRequiredMixin, DetailView):
    model = Trade
    template_name = "monitoring/trade_detail.html"
    context_object_name = "trade"

    def get_queryset(self):
        return Trade.objects.filter(user=self.request.user)


def add_common_metrics(result_dict, entry, stop, target, volume):
    if stop is not None:
        result_dict["Distance to Stop Loss"] = abs(entry - stop)
    if target is not None:
        result_dict["Distance to Target"] = abs(target - entry)
    if stop is not None and volume is not None:
        result_dict["Risk Per Trade (£)"] = abs(entry - stop) * volume


def unified_risk_calculator(request):
    result = None

    if request.method == "POST":
        form = UnifiedRiskForm(request.POST)
        if form.is_valid():
            mode = form.cleaned_data["mode"]
            entry = form.cleaned_data["entry_price"]

            stop = None
            target = None
            volume = None

            try:
                if mode == "volume":
                    risk_amount = form.cleaned_data["risk_amount"]
                    stop = form.cleaned_data["stop_loss_price"]
                    if None in (risk_amount, stop):
                        raise ValueError("Please fill Risk Amount and Stop Loss.")
                    risk_per_unit = abs(entry - stop)
                    volume = Decimal(risk_amount) / risk_per_unit if risk_per_unit != 0 else Decimal("0")
                    result = {
                        "Volume Needed": volume,
                        "Risk Per Unit": risk_per_unit,
                    }
                    add_common_metrics(result, entry, stop, None, volume)

                elif mode == "stoploss":
                    risk_amount = form.cleaned_data["risk_amount"]
                    volume = form.cleaned_data["volume"]
                    if None in (risk_amount, volume):
                        raise ValueError("Please fill Risk Amount and Volume.")
                    risk_per_unit = Decimal(risk_amount) / Decimal(volume)
                    stop = entry - risk_per_unit
                    result = {
                        "Stop Loss Price": stop,
                        "Risk Per Unit": risk_per_unit,
                    }
                    add_common_metrics(result, entry, stop, None, volume)

                elif mode == "target":
                    desired_profit = form.cleaned_data["desired_profit"]
                    volume = form.cleaned_data["volume"]
                    if None in (desired_profit, volume):
                        raise ValueError("Please fill Desired Profit and Volume.")
                    price_diff = Decimal(desired_profit) / Decimal(volume)
                    target = entry + price_diff
                    result = {
                        "Target Price": target,
                        "Price Difference": price_diff,
                    }
                    add_common_metrics(result, entry, None, target, volume)

                elif mode == "riskreward":
                    stop = form.cleaned_data["stop_loss_price"]
                    target = form.cleaned_data["target_price"]
                    if None in (stop, target):
                        raise ValueError("Please fill Stop Loss and Target Price.")
                    risk_per_unit = abs(entry - stop)
                    reward_per_unit = abs(target - entry)
                    ratio = reward_per_unit / risk_per_unit if risk_per_unit != 0 else None
                    result = {
                        "Risk Per Unit": risk_per_unit,
                        "Reward Per Unit": reward_per_unit,
                        "Risk-Reward Ratio": ratio,
                    }
                    add_common_metrics(result, entry, stop, target, None)

                elif mode == "riskpercent":
                    account_size = form.cleaned_data["account_size"]
                    risk_percent = form.cleaned_data["risk_percent"]
                    stop = form.cleaned_data["stop_loss_price"]
                    if None in (account_size, risk_percent, stop):
                        raise ValueError("Please fill Account Size, Risk %, and Stop Loss.")
                    risk_amount = Decimal(account_size) * (Decimal(risk_percent) / Decimal(100))
                    risk_per_unit = abs(entry - stop)
                    volume = risk_amount / risk_per_unit if risk_per_unit != 0 else Decimal("0")
                    result = {
                        "Risk Amount": risk_amount,
                        "Volume Allowed": volume,
                        "Risk Per Unit": risk_per_unit,
                    }
                    add_common_metrics(result, entry, stop, None, volume)

                elif mode == "targetprofitvolume":
                    desired_profit = form.cleaned_data["desired_profit"]
                    target = form.cleaned_data["target_price"]
                    if None in (desired_profit, target):
                        raise ValueError("Please fill Desired Profit and Target Price.")
                    distance_to_tp = abs(target - entry)
                    volume = Decimal(desired_profit) / distance_to_tp if distance_to_tp != 0 else Decimal("0")
                    result = {
                        "Volume Needed": volume,
                        "Distance to Target": distance_to_tp,
                    }
                    add_common_metrics(result, entry, None, target, volume)

            except (InvalidOperation, ValueError) as exc:
                form.add_error(None, str(exc))
    else:
        form = UnifiedRiskForm()

    return render(
        request,
        "monitoring/risk_calculator.html",
        {
            "form": form,
            "result": result,
        },
    )


@login_required
def alert_create(request):
    if request.method == "POST":
        form = AlertForm(request.POST)
        if form.is_valid():
            create_user_alert_from_form(request.user, form)
            return redirect("monitoring:alert_list")
    else:
        form = AlertForm()

    return render(request, "monitoring/alert_form.html", {"form": form})


@login_required
def alert_list(request):
    alerts = request.user.alerts.select_related("asset").all()
    return render(request, "monitoring/alert_list.html", {"alerts": alerts})


@login_required
def create_alert(request):
    if request.method == "POST":
        form = AlertForm(request.POST)
        if form.is_valid():
            create_user_alert_from_form(request.user, form)
            return redirect("monitoring:dashboard")
    else:
        form = AlertForm()

    return render(request, "monitoring/create_alert.html", {"form": form})


@login_required
def close_trade(request, pk):
    trade = get_object_or_404(Trade, pk=pk, user=request.user)

    if trade.is_closed:
        messages.warning(request, "This trade is already closed.")
        return redirect("monitoring:trade_detail", pk=trade.pk)

    latest_snapshot = (
        PriceSnapshot.objects
        .filter(asset=trade.asset)
        .order_by("-timestamp")
        .first()
    )

    if not latest_snapshot:
        messages.error(request, "No price data available to close the trade.")
        return redirect("monitoring:trade_detail", pk=trade.pk)

    trade.exit_price = latest_snapshot.price
    trade.closed_at = timezone.now()
    trade.save()

    messages.success(request, f"Trade closed at {latest_snapshot.price}.")
    return redirect("monitoring:trade_detail", pk=trade.pk)


@login_required
def export_trades_csv(request):
    trades = Trade.objects.filter(user=request.user).order_by("-opened_at")

    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="trades.csv"'},
    )

    writer = csv.writer(response)
    writer.writerow(
        [
            "Asset",
            "Type",
            "Quantity",
            "Entry Price",
            "Exit Price",
            "P&L (£)",
            "P&L %",
            "Opened At",
            "Closed At",
            "Notes",
        ]
    )

    for trade in trades:
        writer.writerow(
            [
                trade.asset.symbol,
                trade.trade_type,
                trade.quantity,
                trade.entry_price,
                trade.exit_price or "",
                f"{trade.pnl:.2f}" if trade.pnl is not None else "",
                f"{trade.pnl_percentage:.2f}%" if trade.pnl_percentage is not None else "",
                trade.opened_at.strftime("%Y-%m-%d %H:%M"),
                trade.closed_at.strftime("%Y-%m-%d %H:%M") if trade.closed_at else "",
                trade.notes,
            ]
        )

    return response


@login_required
def export_trades_excel(request):
    trades = Trade.objects.filter(user=request.user).order_by("-opened_at")

    data = []
    for trade in trades:
        opened_at_naive = trade.opened_at.replace(tzinfo=None) if trade.opened_at else None
        closed_at_naive = trade.closed_at.replace(tzinfo=None) if trade.closed_at else None

        data.append(
            {
                "Asset": trade.asset.symbol,
                "Type": trade.trade_type,
                "Quantity": trade.quantity,
                "Entry Price": trade.entry_price,
                "Exit Price": trade.exit_price,
                "P&L (£)": f"{trade.pnl:.2f}" if trade.pnl is not None else "",
                "P&L %": f"{trade.pnl_percentage:.2f}%" if trade.pnl_percentage is not None else "",
                "Opened At": opened_at_naive,
                "Closed At": closed_at_naive,
                "Notes": trade.notes,
            }
        )

    df = pd.DataFrame(data)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Trades")

    buffer.seek(0)

    response = HttpResponse(
        buffer,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="trades.xlsx"'
    return response


@login_required
def export_prices_csv(request):
    snapshots = (
        PriceSnapshot.objects
        .select_related("asset")
        .order_by("-timestamp")
    )

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