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
    alerts = request.user.alerts.select_related("asset").all()
    alert_summary = get_alert_summary(request.user)

    context = {
        "alerts": alerts,
        "active_alerts_count": alert_summary["active_count"],
        "triggered_alerts_count": alert_summary["triggered_count"],
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