from decimal import Decimal, InvalidOperation
import logging

from django.conf import settings
from django.core.mail import send_mail

from .models import Alert

logger = logging.getLogger(__name__)


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
    if alert.direction == "above":
        return price >= alert.target_price
    if alert.direction == "below":
        return price <= alert.target_price
    return False


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

    alerts = Alert.objects.filter(asset=asset, is_triggered=False).select_related("user", "asset")
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