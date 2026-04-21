from ..models import WatchlistItem


def get_watchlist_for_user(user, limit=8):
    if not getattr(user, "is_authenticated", False):
        return WatchlistItem.objects.none()

    return (
        WatchlistItem.objects.filter(user=user)
        .select_related("asset")
        .order_by("asset__symbol")[:limit]
    )


def add_asset_to_watchlist(user, asset, note=""):
    watchlist_item, _ = WatchlistItem.objects.get_or_create(
        user=user,
        asset=asset,
        defaults={"note": note},
    )
    return watchlist_item


def remove_asset_from_watchlist(user, asset):
    deleted_count, _ = WatchlistItem.objects.filter(user=user, asset=asset).delete()
    return deleted_count