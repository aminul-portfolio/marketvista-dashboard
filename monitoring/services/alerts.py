"""Alert services for threshold review, summaries, and notifications."""

import logging
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction

from ..models import Alert

logger = logging.getLogger(__name__)


def _normalize_decimal(value):
    """
    Convert any incoming numeric value into Decimal safely.
    """
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _should_trigger(alert, price: Decimal) -> bool:
    """
    Decide whether a specific alert should trigger against a normalized price.
    """
    if price is None:
        return False

    if alert.direction == "above":
        return price >= alert.target_price

    if alert.direction == "below":
        return price <= alert.target_price

    return False


def _latest_price_for_alert(alert):
    """
    Return the latest stored snapshot price for the alert's asset.

    This uses the same snapshot source shown elsewhere in MarketVista, so the
    alert review page can show status and current price consistently.
    """
    latest_snapshot = alert.asset.price_snapshots.order_by("-timestamp").first()

    if not latest_snapshot:
        return None

    return _normalize_decimal(latest_snapshot.price)


def sync_user_alert_states(user):
    """
    Persist any alert that has crossed its threshold according to the latest
    stored snapshot.

    This is intentionally conservative:
    - It only moves non-triggered alerts into triggered state.
    - It never moves a triggered alert back to pending.
    - It does not send email from the page-view path.
    """
    if not getattr(user, "is_authenticated", False):
        return 0

    alerts = (
        Alert.objects.filter(user=user, is_triggered=False)
        .select_related("asset")
        .order_by("-created_at")
    )

    updated_count = 0

    for alert in alerts:
        current_price = _latest_price_for_alert(alert)

        if not _should_trigger(alert, current_price):
            continue

        alert.is_triggered = True
        alert.save(update_fields=["is_triggered"])
        updated_count += 1

    return updated_count


def _decorate_alert_for_review(alert):
    """
    Attach display-only values used by alert_list.html.

    These attributes keep the premium template simple and ensure the KPI strip
    and visible table rows use the same status state.
    """
    current_price = _latest_price_for_alert(alert)

    alert.current_price = current_price
    alert.review_is_triggered = bool(alert.is_triggered)
    alert.review_status = "triggered" if alert.review_is_triggered else "pending"
    alert.review_status_label = "TRIGGERED" if alert.review_is_triggered else "PENDING"
    alert.review_status_class = "danger" if alert.review_is_triggered else "neutral"

    return alert


def get_alert_review_rows(user):
    """
    Return alert rows for the alert review page.

    The function first synchronizes crossed thresholds, then returns the rows
    decorated with display values. The table and summary should both use this
    same list.
    """
    if not getattr(user, "is_authenticated", False):
        return []

    sync_user_alert_states(user)

    alerts = list(
        Alert.objects.filter(user=user)
        .select_related("asset")
        .order_by("-created_at")
    )

    return [_decorate_alert_for_review(alert) for alert in alerts]


def get_active_alert_count(user):
    if not getattr(user, "is_authenticated", False):
        return 0

    return get_alert_summary(user)["pending_count"]


def get_triggered_alerts(user, limit=10):
    if not getattr(user, "is_authenticated", False):
        return []

    return [
        alert for alert in get_alert_review_rows(user)
        if alert.review_is_triggered
    ][:limit]


def get_alert_summary(user, alert_rows=None):
    """
    Return consistent alert counts.

    If alert_rows is supplied, the counts are built from exactly the same rows
    shown in the table. This is the key consistency rule for the Alerts page.
    """
    if not getattr(user, "is_authenticated", False):
        return {
            "total_count": 0,
            "row_count": 0,
            "active_count": 0,
            "pending_count": 0,
            "triggered_count": 0,
            "recent_triggered": [],
        }

    rows = list(alert_rows) if alert_rows is not None else get_alert_review_rows(user)

    total_count = len(rows)
    triggered_count = sum(1 for alert in rows if alert.review_is_triggered)
    pending_count = total_count - triggered_count
    recent_triggered = [alert for alert in rows if alert.review_is_triggered][:5]

    return {
        "total_count": total_count,
        "row_count": total_count,
        "active_count": pending_count,  # backward-compatible alias
        "pending_count": pending_count,
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
        current_price = _latest_price_for_alert(alert)

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


def send_alert_email(user, alert, current_price=None):
    """
    Send an email notification when an alert is triggered.
    """
    if not user.email:
        logger.warning(
            "Cannot send alert email: user '%s' has no email set.",
            user.username,
        )
        return

    direction_text = "above" if alert.direction == "above" else "below"

    subject = f"Price Alert Triggered — {alert.asset.symbol}"
    message_lines = [
        f"Hi {user.username},",
        "",
        f"Your MarketVista alert for {alert.asset.symbol} has been triggered.",
        f"Direction: {direction_text}",
        f"Target price: {alert.target_price}",
    ]

    if current_price is not None:
        message_lines.append(f"Observed price: {current_price}")

    message_lines.extend(
        [
            "",
            "This alert is now marked as triggered in MarketVista Dashboard.",
            "",
            "— MarketVista Dashboard",
        ]
    )

    message = "\n".join(message_lines)

    logger.info(
        "Preparing alert email for %s on %s",
        user.email,
        alert.asset.symbol,
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info(
            "Alert email sent to %s for %s",
            user.email,
            alert.asset.symbol,
        )
    except Exception:
        logger.exception(
            "Failed to send alert email to %s for %s",
            user.email,
            alert.asset.symbol,
        )


def check_alerts_for_asset(asset, latest_price):
    """
    Check all non-triggered alerts for a given asset and trigger matching ones.
    """
    normalized_price = _normalize_decimal(latest_price)

    if normalized_price is None:
        logger.warning(
            "Skipping alert check for %s due to invalid latest price: %r",
            asset.symbol,
            latest_price,
        )
        return 0

    alerts = Alert.objects.filter(asset=asset, is_triggered=False).select_related(
        "user",
        "asset",
    )
    triggered_count = 0

    for alert in alerts:
        logger.info(
            "Checking alert | asset=%s user=%s direction=%s target=%s price=%s",
            alert.asset.symbol,
            alert.user.username,
            alert.direction,
            alert.target_price,
            normalized_price,
        )

        if not _should_trigger(alert, normalized_price):
            continue

        alert.is_triggered = True
        alert.save(update_fields=["is_triggered"])
        triggered_count += 1

        logger.info(
            "Triggered alert | asset=%s user=%s target=%s price=%s",
            alert.asset.symbol,
            alert.user.username,
            alert.target_price,
            normalized_price,
        )

        send_alert_email(
            user=alert.user,
            alert=alert,
            current_price=normalized_price,
        )

    return triggered_count
