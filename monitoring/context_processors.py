from .models import Alert, MarketSignal, WatchlistItem


def active_alert_count(request):
    """
    Expose sidebar badge counts to all templates globally.
    Provides: alert_count, sidebar_elevated_count, watchlist_count
    """
    user = getattr(request, "user", None)

    if not user or not user.is_authenticated:
        return {
            "alert_count": 0,
            "sidebar_elevated_count": 0,
            "watchlist_count": 0,
        }

    try:
        alert_count = Alert.objects.filter(
            user=user,
            is_triggered=False,
        ).count()
    except Exception:
        alert_count = 0

    try:
        sidebar_elevated_count = MarketSignal.objects.filter(
            is_active=True,
            severity="ELEVATED",
        ).count()
    except Exception:
        sidebar_elevated_count = 0

    try:
        watchlist_count = WatchlistItem.objects.filter(user=user).count()
    except Exception:
        watchlist_count = 0

    return {
        "alert_count": alert_count,
        "sidebar_elevated_count": sidebar_elevated_count,
        "watchlist_count": watchlist_count,
    }
