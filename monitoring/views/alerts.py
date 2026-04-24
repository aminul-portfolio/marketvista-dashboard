"""Views for alert management and triggered alert endpoints."""

import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render

from ..forms import AlertForm
from ..services.alerts import (
    create_user_alert_from_form,
    fetch_and_acknowledge_triggered_alerts,
    get_active_alert_count,
    get_alert_review_rows,
    get_alert_summary,
)
from ..services.market import get_freshness_signal
from ..services.signals import get_active_signals
from ..services.watchlist import get_watchlist_count

logger = logging.getLogger(__name__)


@login_required
def create_alert(request):
    if request.method == "POST":
        form = AlertForm(request.POST)
        if form.is_valid():
            create_user_alert_from_form(request.user, form)
            return redirect("monitoring:alert_list")
    else:
        form = AlertForm()

    context = {
        "form": form,
        "freshness_signal": get_freshness_signal(),
        "watchlist_count": get_watchlist_count(request.user),
        "sidebar_elevated_count": get_active_signals(severity="ELEVATED").count(),
        "active_alerts_count": get_active_alert_count(request.user),
    }
    return render(request, "monitoring/create_alert.html", context)


@login_required
def alert_list(request):
    """
    Alert review page.

    Important:
    The alert table and KPI strip must be built from the same reviewed alert
    rows. This prevents a reviewer-visible contradiction such as:
    Triggered = 0 while the table displays a TRIGGERED row.
    """
    alerts = get_alert_review_rows(request.user)
    alert_summary = get_alert_summary(request.user, alert_rows=alerts)

    context = {
        "alerts": alerts,

        # Preferred explicit names for the premium alert template.
        "total_alerts_count": alert_summary["total_count"],
        "triggered_alerts_count": alert_summary["triggered_count"],
        "pending_alerts_count": alert_summary["pending_count"],
        "alert_rows_count": alert_summary["row_count"],

        # Compatibility aliases for older template variable names.
        "total_alerts": alert_summary["total_count"],
        "triggered_count": alert_summary["triggered_count"],
        "pending_count": alert_summary["pending_count"],
        "alert_rows": alert_summary["row_count"],

        # Sidebar / global shell values.
        "active_alerts_count": alert_summary["pending_count"],
        "watchlist_count": get_watchlist_count(request.user),
        "sidebar_elevated_count": get_active_signals(severity="ELEVATED").count(),
        "freshness_signal": get_freshness_signal(),
    }
    return render(request, "monitoring/alert_list.html", context)


@login_required
def triggered_alerts_api(request):
    try:
        triggered = fetch_and_acknowledge_triggered_alerts(request.user)
        return JsonResponse({"alerts": triggered})
    except Exception as exc:
        logger.exception("Error in triggered_alerts_api")
        return JsonResponse({"error": str(exc)}, status=500)
