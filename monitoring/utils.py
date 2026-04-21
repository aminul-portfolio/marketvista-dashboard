# utils.py
from django.core.mail import send_mail
from django.conf import settings
from .models import Alert
from decimal import Decimal
import logging
import time

logger = logging.getLogger(__name__)

def send_alert_email(user, alert):
    subject = f"🚨 Price Alert Triggered for {alert.asset.symbol}"
    direction_text = "above" if alert.direction == 'above' else "below"
    message = (
        f"Hi {user.username},\n\n"
        f"The price of {alert.asset.symbol} has just moved {direction_text} your alert target of {alert.target_price}.\n\n"
        f"Current condition has been met.\n\n"
        f"— MarketPulse Team"
    )

    logger.info(f"📤 Preparing to send email to {user.email}")

    if not user.email:
        logger.warning(f"⚠️ Cannot send alert email: User {user.username} has no email set.")
        return

    try:
        time.sleep(1)  # optional buffer to avoid throttling
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        logger.info(f"✅ Alert email sent to {user.email} for {alert.asset.symbol}")
    except Exception as e:
        logger.error(f"❌ Failed to send alert email to {user.email}: {e}")

def check_alerts_for_asset(asset, latest_price):
    alerts = Alert.objects.filter(asset=asset, is_triggered=False)
    price = Decimal(str(latest_price))

    for alert in alerts:
        logger.info(f"🔍 Checking alert for {alert.asset.symbol} | Target: {alert.target_price} | Direction: {alert.direction} | Price: {price}")

        should_trigger = (
            alert.direction == 'above' and price > alert.target_price or
            alert.direction == 'below' and price < alert.target_price
        )

        if should_trigger:
            alert.is_triggered = True
            alert.save(update_fields=['is_triggered'])
            logger.info(f"🚨 Triggered alert for {alert.asset.symbol} (User: {alert.user.email})")
            send_alert_email(alert.user, alert)
