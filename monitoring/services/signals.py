from datetime import timedelta
from decimal import Decimal
from statistics import pstdev

from django.utils.timezone import now

from ..models import Asset, MarketSignal, PriceOHLC, WatchlistItem
INFO_MOVE_THRESHOLD_PCT = 3.0
WATCHLIST_MOVE_THRESHOLD_PCT = 5.0
ELEVATED_MOVE_THRESHOLD_PCT = 8.0

WATCHLIST_VOLATILITY_RATIO = 1.5
ELEVATED_VOLATILITY_RATIO = 2.0

KNOWN_SIGNAL_TYPES = {
    "ma_crossover",
    "pct_move_3d",
    "volatility_spike",
}


def _mean(values):
    return sum(values) / len(values) if values else 0.0


def _pct_change(new_value, old_value):
    if old_value == 0:
        return 0.0
    return ((new_value - old_value) / old_value) * 100.0


def _latest_ohlc_rows(asset, limit=60):
    rows = list(PriceOHLC.objects.filter(asset=asset).order_by("-timestamp")[:limit])
    rows.reverse()
    return rows


def _build_signal_payload(
    signal_type,
    severity,
    title,
    details,
    metric_value,
    signal_timestamp,
):
    return {
        "signal_type": signal_type,
        "severity": severity,
        "title": title,
        "details": details,
        "metric_value": metric_value,
        "signal_timestamp": signal_timestamp,
    }


def _compute_ma_crossover_signal(closes, latest_timestamp):
    """
    Rules aligned to the monitoring checklist:
    - crossover day -> WATCHLIST
    - confirmed second day -> ELEVATED
    """
    if len(closes) < 21:
        return None

    prev_short_ma = _mean(closes[-6:-1])
    prev_long_ma = _mean(closes[-21:-1])
    curr_short_ma = _mean(closes[-5:])
    curr_long_ma = _mean(closes[-20:])
    spread_pct = _pct_change(curr_short_ma, curr_long_ma)

    if prev_short_ma <= prev_long_ma and curr_short_ma > curr_long_ma:
        return _build_signal_payload(
            signal_type="ma_crossover",
            severity="WATCHLIST",
            title="Bullish 5d/20d MA crossover",
            details=(
                f"5-day MA crossed above 20-day MA by {spread_pct:.2f}%. "
                "Monitor for confirmation."
            ),
            metric_value=spread_pct,
            signal_timestamp=latest_timestamp,
        )

    if prev_short_ma >= prev_long_ma and curr_short_ma < curr_long_ma:
        return _build_signal_payload(
            signal_type="ma_crossover",
            severity="WATCHLIST",
            title="Bearish 5d/20d MA crossover",
            details=(
                f"5-day MA crossed below 20-day MA by {spread_pct:.2f}%. "
                "Monitor for confirmation."
            ),
            metric_value=spread_pct,
            signal_timestamp=latest_timestamp,
        )

    if len(closes) < 22:
        return None

    two_day_short_ma = _mean(closes[-7:-2])
    two_day_long_ma = _mean(closes[-22:-2])

    if (
        two_day_short_ma <= two_day_long_ma
        and prev_short_ma > prev_long_ma
        and curr_short_ma > curr_long_ma
    ):
        return _build_signal_payload(
            signal_type="ma_crossover",
            severity="ELEVATED",
            title="Bullish crossover confirmed",
            details=(
                f"5-day MA remained above 20-day MA for a second period. "
                f"Current spread is {spread_pct:.2f}%."
            ),
            metric_value=spread_pct,
            signal_timestamp=latest_timestamp,
        )

    if (
        two_day_short_ma >= two_day_long_ma
        and prev_short_ma < prev_long_ma
        and curr_short_ma < curr_long_ma
    ):
        return _build_signal_payload(
            signal_type="ma_crossover",
            severity="ELEVATED",
            title="Bearish crossover confirmed",
            details=(
                f"5-day MA remained below 20-day MA for a second period. "
                f"Current spread is {spread_pct:.2f}%."
            ),
            metric_value=spread_pct,
            signal_timestamp=latest_timestamp,
        )

    return None


def _compute_pct_move_signal(closes, latest_timestamp):
    """
    3-day move thresholds:
    - ±3% -> INFO
    - ±5% -> WATCHLIST
    - ±8% -> ELEVATED
    """
    if len(closes) < 4:
        return None

    move_3d_pct = _pct_change(closes[-1], closes[-4])
    abs_move = abs(move_3d_pct)

    if abs_move < INFO_MOVE_THRESHOLD_PCT:
        return None

    if abs_move >= ELEVATED_MOVE_THRESHOLD_PCT:
        severity = "ELEVATED"
    elif abs_move >= WATCHLIST_MOVE_THRESHOLD_PCT:
        severity = "WATCHLIST"
    else:
        severity = "INFO"

    direction = "up" if move_3d_pct >= 0 else "down"

    return _build_signal_payload(
        signal_type="pct_move_3d",
        severity=severity,
        title=f"3-day move {move_3d_pct:+.2f}%",
        details=(
            f"Asset moved {move_3d_pct:+.2f}% over the last 3 periods "
            f"({direction} move)."
        ),
        metric_value=move_3d_pct,
        signal_timestamp=latest_timestamp,
    )


def _compute_volatility_spike_signal(closes, latest_timestamp):
    """
    Volatility spike:
    - current 10-period std dev of returns
    - compared with prior 30-period std dev of returns
    """
    if len(closes) < 41:
        return None

    returns = []
    for index in range(1, len(closes)):
        previous_close = closes[index - 1]
        current_close = closes[index]
        returns.append(_pct_change(current_close, previous_close))

    if len(returns) < 40:
        return None

    current_window = returns[-10:]
    baseline_window = returns[-40:-10]

    current_vol = pstdev(current_window) if len(current_window) >= 2 else 0.0
    baseline_vol = pstdev(baseline_window) if len(baseline_window) >= 2 else 0.0

    if baseline_vol <= 0:
        return None

    ratio = current_vol / baseline_vol

    if ratio < WATCHLIST_VOLATILITY_RATIO:
        return None

    severity = (
        "ELEVATED"
        if ratio >= ELEVATED_VOLATILITY_RATIO
        else "WATCHLIST"
    )

    return _build_signal_payload(
        signal_type="volatility_spike",
        severity=severity,
        title=f"Volatility spike ({ratio:.2f}x baseline)",
        details=(
            f"Recent realized volatility is {ratio:.2f}x the trailing baseline."
        ),
        metric_value=ratio,
        signal_timestamp=latest_timestamp,
    )


def compute_basic_signals(asset):
    rows = _latest_ohlc_rows(asset, limit=60)
    if len(rows) < 21:
        return []

    closes = [float(row.close) for row in rows]
    latest_timestamp = rows[-1].timestamp
    results = []

    ma_signal = _compute_ma_crossover_signal(closes, latest_timestamp)
    if ma_signal:
        results.append(ma_signal)

    pct_move_signal = _compute_pct_move_signal(closes, latest_timestamp)
    if pct_move_signal:
        results.append(pct_move_signal)

    volatility_signal = _compute_volatility_spike_signal(closes, latest_timestamp)
    if volatility_signal:
        results.append(volatility_signal)

    return results


def compute_asset_signals(asset):
    """
    Backward-compatible alias for existing callers.
    """
    return compute_basic_signals(asset)


def refresh_asset_signals(asset):
    current_signals = compute_basic_signals(asset)
    active_types = set()

    for signal in current_signals:
        active_types.add(signal["signal_type"])

        MarketSignal.objects.filter(
            asset=asset,
            signal_type=signal["signal_type"],
            is_active=True,
        ).exclude(signal_timestamp=signal["signal_timestamp"]).update(is_active=False)

        MarketSignal.objects.update_or_create(
            asset=asset,
            signal_type=signal["signal_type"],
            signal_timestamp=signal["signal_timestamp"],
            defaults={
                "severity": signal["severity"],
                "title": signal["title"],
                "details": signal["details"],
                "metric_value": Decimal(str(round(signal["metric_value"], 8))),
                "is_active": True,
            },
        )

    stale_types = KNOWN_SIGNAL_TYPES - active_types
    if stale_types:
        MarketSignal.objects.filter(
            asset=asset,
            signal_type__in=stale_types,
            is_active=True,
        ).update(is_active=False)

    return current_signals


def refresh_signals_for_assets(assets=None):
    if assets is None:
        assets = Asset.objects.all()

    refreshed = []
    for asset in assets:
        refreshed.extend(refresh_asset_signals(asset))
    return refreshed


def get_latest_signals(limit=8):
    return (
        MarketSignal.objects.filter(is_active=True)
        .select_related("asset")
        .order_by("-signal_timestamp", "-created_at")[:limit]
    )


def get_signal_history(asset, days=30):
    cutoff = now() - timedelta(days=days)
    return (
        MarketSignal.objects.filter(asset=asset, signal_timestamp__gte=cutoff)
        .select_related("asset")
        .order_by("-signal_timestamp", "-created_at")
    )


def get_active_signals(severity=None):
    queryset = (
        MarketSignal.objects.filter(is_active=True)
        .select_related("asset")
        .order_by("-signal_timestamp", "-created_at")
    )
    if severity:
        queryset = queryset.filter(severity=severity)
    return queryset


def flag_assets_for_riskwise(user):
    if not getattr(user, "is_authenticated", False):
        return []

    watchlisted_asset_ids = WatchlistItem.objects.filter(user=user).values_list(
        "asset_id",
        flat=True,
    )

    return list(
        MarketSignal.objects.filter(
            asset_id__in=watchlisted_asset_ids,
            is_active=True,
            severity="ELEVATED",
        )
        .select_related("asset")
        .values_list("asset__symbol", flat=True)
        .distinct()
    )