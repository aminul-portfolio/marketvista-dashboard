"""
Future task module for MarketVista live ingestion and notifications.

Current repo state:
- reviewer-ready seeded demo
- tested monitoring workflows
- no active Celery-backed ingestion path exposed as part of the supported reviewer flow

When live market data ingestion is introduced in a future version, this module
will become the home for background tasks such as:

- fetch_and_store_ohlc
- fetch_snapshot_prices
- trigger_alert_checks
- send_user_notifications

Recommended future direction:
- Celery + Redis for scheduled/background execution
- provider-safe polling intervals
- retry/error handling for external APIs
- idempotent persistence for OHLC and snapshot rows
- alert checks routed through monitoring.services.alerts
"""

__all__ = []