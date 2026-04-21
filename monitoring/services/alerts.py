from django.db import transaction

from ..models import Alert


def get_active_alert_count(user):
    if not getattr(user, "is_authenticated", False):
        return 0
    return Alert.objects.filter(user=user, is_triggered=False).count()


def get_triggered_alerts(user, limit=10):
    if not getattr(user, "is_authenticated", False):
        return Alert.objects.none()

    return (
        Alert.objects.filter(user=user, is_triggered=True)
        .select_related("asset")
        .order_by("-created_at")[:limit]
    )


def get_alert_summary(user):
    if not getattr(user, "is_authenticated", False):
        return {
            "active_count": 0,
            "triggered_count": 0,
            "recent_triggered": [],
        }

    active_count = Alert.objects.filter(user=user, is_triggered=False).count()
    triggered_count = Alert.objects.filter(user=user, is_triggered=True).count()
    recent_triggered = list(get_triggered_alerts(user, limit=5))

    return {
        "active_count": active_count,
        "triggered_count": triggered_count,
        "recent_triggered": recent_triggered,
    }


def create_user_alert_from_form(user, form):
    alert = form.save(commit=False)
    alert.user = user
    alert.save()
    return alert


def fetch_and_acknowledge_triggered_alerts(user):
    if not getattr(user, "is_authenticated", False):
        return []

    alerts = (
        Alert.objects.filter(
            user=user,
            is_triggered=True,
            is_notified=False,
        )
        .select_related("asset")
        .order_by("-created_at")
    )

    payload = []

    for alert in alerts:
        latest_snapshot = alert.asset.price_snapshots.order_by("-timestamp").first()
        current_price = latest_snapshot.price if latest_snapshot else None

        payload.append(
            {
                "symbol": alert.asset.symbol,
                "asset_name": alert.asset.name,
                "price": str(current_price) if current_price is not None else None,
                "direction": alert.direction,
                "target": str(alert.target_price),
                "created_at": alert.created_at.isoformat(),
            }
        )

        with transaction.atomic():
            alert.is_notified = True
            alert.save(update_fields=["is_notified"])

    return payload