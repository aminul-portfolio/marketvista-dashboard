from ..models import WatchlistItem


def get_watchlist_for_user(user, limit=None):
    if not getattr(user, "is_authenticated", False):
        return WatchlistItem.objects.none()

    queryset = (
        WatchlistItem.objects.filter(user=user)
        .select_related("asset")
        .order_by("asset__symbol")
    )

    if limit:
        return queryset[:limit]
    return queryset


def get_watchlist_count(user):
    if not getattr(user, "is_authenticated", False):
        return 0
    return WatchlistItem.objects.filter(user=user).count()


def is_on_watchlist(user, asset):
    if not getattr(user, "is_authenticated", False):
        return False

    return WatchlistItem.objects.filter(user=user, asset=asset).exists()


def add_asset_to_watchlist(user, asset, note=""):
    watchlist_item, created = WatchlistItem.objects.get_or_create(
        user=user,
        asset=asset,
        defaults={"note": note},
    )

    if not created and note and watchlist_item.note != note:
        watchlist_item.note = note
        watchlist_item.save(update_fields=["note"])

    return watchlist_item


def remove_asset_from_watchlist(user, asset):
    deleted_count, _ = WatchlistItem.objects.filter(user=user, asset=asset).delete()
    return deleted_count