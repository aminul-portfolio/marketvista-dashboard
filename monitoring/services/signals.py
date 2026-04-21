from decimal import Decimal
from statistics import pstdev

from ..models import Asset, MarketSignal, PriceOHLC

MOVE_THRESHOLD_PCT = 3.0
ELEVATED_MOVE_THRESHOLD_PCT = 5.0
VOLATILITY_SPIKE_RATIO = 1.5
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


def _latest_ohlc_rows(asset, limit=40):
    rows = list(
        PriceOHLC.objects.filter(asset=asset)
        .order_by("-timestamp")[:limit]
    )
    rows.reverse()
    return rows


def compute_asset_signals(asset):
    rows = _latest_ohlc_rows(asset)
    if len(rows) < 20:
        return []

    closes = [float(row.close) for row in rows]
    latest_timestamp = rows[-1].timestamp
    results = []

    prev_short_ma = _mean(closes[-6:-1])
    prev_long_ma = _mean(closes[-21:-1])
    curr_short_ma = _mean(closes[-5:])
    curr_long_ma = _mean(closes[-20:])

    if prev_short_ma <= prev_long_ma and curr_short_ma > curr_long_ma:
        gap_pct = _pct_change(curr_short_ma, curr_long_ma)
        results.append(
            {
                "signal_type": "ma_crossover",
                "severity": "INFO" if abs(gap_pct) < 0.35 else "WATCHLIST",
                "title": "Bullish 5d/20d MA crossover",
                "details": f"5-day MA crossed above 20-day MA by {gap_pct:.2f}%.",
                "metric_value": gap_pct,
                "signal_timestamp": latest_timestamp,
            }
        )
    elif prev_short_ma >= prev_long_ma and curr_short_ma < curr_long_ma:
        gap_pct = _pct_change(curr_short_ma, curr_long_ma)
        results.append(
            {
                "signal_type": "ma_crossover",
                "severity": "INFO" if abs(gap_pct) < 0.35 else "WATCHLIST",
                "title": "Bearish 5d/20d MA crossover",
                "details": f"5-day MA crossed below 20-day MA by {gap_pct:.2f}%.",
                "metric_value": gap_pct,
                "signal_timestamp": latest_timestamp,
            }
        )

    if len(closes) >= 4:
        move_3d_pct = _pct_change(closes[-1], closes[-4])
        if abs(move_3d_pct) >= MOVE_THRESHOLD_PCT:
            results.append(
                {
                    "signal_type": "pct_move_3d",
                    "severity": "WATCHLIST" if abs(move_3d_pct) < ELEVATED_MOVE_THRESHOLD_PCT else "ELEVATED",
                    "title": f"3-day move {move_3d_pct:+.2f}%",
                    "details": f"Asset moved {move_3d_pct:+.2f}% over the last 3 periods.",
                    "metric_value": move_3d_pct,
                    "signal_timestamp": latest_timestamp,
                }
            )

    returns = []
    for index in range(1, len(closes)):
        previous_close = closes[index - 1]
        current_close = closes[index]
        returns.append(_pct_change(current_close, previous_close))

    if len(returns) >= 20:
        recent_window = returns[-5:]
        baseline_window = returns[-20:-5]

        recent_vol = pstdev(recent_window) if len(recent_window) >= 2 else 0.0
        baseline_vol = pstdev(baseline_window) if len(baseline_window) >= 2 else 0.0

        if baseline_vol > 0:
            ratio = recent_vol / baseline_vol
            if ratio >= VOLATILITY_SPIKE_RATIO:
                results.append(
                    {
                        "signal_type": "volatility_spike",
                        "severity": "WATCHLIST" if ratio < ELEVATED_VOLATILITY_RATIO else "ELEVATED",
                        "title": f"Volatility spike ({ratio:.2f}x baseline)",
                        "details": f"Recent realized volatility is {ratio:.2f}x the trailing baseline.",
                        "metric_value": ratio,
                        "signal_timestamp": latest_timestamp,
                    }
                )

    return results


def refresh_asset_signals(asset):
    current_signals = compute_asset_signals(asset)
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
            title=signal["title"],
            defaults={
                "severity": signal["severity"],
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