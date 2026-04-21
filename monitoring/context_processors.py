from .models import Alert


def active_alert_count(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {"alert_count": 0}

    alert_count = Alert.objects.filter(
        user=request.user,
        is_triggered=False,
    ).count()

    return {"alert_count": alert_count}