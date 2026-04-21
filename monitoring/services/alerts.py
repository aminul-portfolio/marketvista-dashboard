from django.db import transaction

from ..models import Alert


def get_active_alert_count(user):
    if not getattr(user, "is_authenticated", False):
        return 0
    return Alert.objects.filter(user=user, is_triggered=False).count()


def create_user_alert_from_form(user, form):
    alert = form.save(commit=False)
    alert.user = user
    alert.save()
    return alert


def fetch_and_acknowledge_triggered_alerts(user):
    alerts = (
        Alert.objects.filter(
            user=user,
            is_triggered=True,
            is_notified=False,
        )
        .select_related("asset")
    )

    payload = []

    for alert in alerts:
        latest = alert.asset.price_snapshots.order_by("-timestamp").first()
        if not latest:
            continue

        payload.append(
            {
                "symbol": alert.asset.symbol,
                "price": str(latest.price),
                "direction": alert.direction,
                "target": str(alert.target_price),
            }
        )

        with transaction.atomic():
            alert.is_notified = True
            alert.save(update_fields=["is_notified"])

    return payload