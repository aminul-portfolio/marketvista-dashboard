from django.contrib import admin

from .models import (
    Alert,
    Asset,
    MarketSignal,
    PriceOHLC,
    PriceSnapshot,
    WatchlistItem,
)


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("symbol", "name", "asset_type")
    search_fields = ("symbol", "name")
    list_filter = ("asset_type",)
    ordering = ("symbol",)


@admin.register(PriceSnapshot)
class PriceSnapshotAdmin(admin.ModelAdmin):
    list_display = ("asset", "price", "timestamp")
    search_fields = ("asset__symbol", "asset__name")
    list_filter = ("asset",)
    ordering = ("-timestamp",)


@admin.register(PriceOHLC)
class PriceOHLCAdmin(admin.ModelAdmin):
    list_display = ("asset", "timestamp", "open", "high", "low", "close", "volume", "source")
    search_fields = ("asset__symbol", "asset__name", "source")
    list_filter = ("asset", "source")
    ordering = ("-timestamp",)


@admin.register(MarketSignal)
class MarketSignalAdmin(admin.ModelAdmin):
    list_display = ("asset", "signal_type", "severity", "is_active", "signal_timestamp")
    search_fields = ("asset__symbol", "asset__name", "signal_type", "title", "details")
    list_filter = ("severity", "signal_type", "is_active")
    ordering = ("-signal_timestamp",)


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("id", "asset")
    search_fields = ("asset__symbol", "asset__name")
    list_filter = ("asset",)
    ordering = ("-id",)


@admin.register(WatchlistItem)
class WatchlistItemAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "asset")
    search_fields = ("user__username", "asset__symbol", "asset__name", "note")
    list_filter = ("asset",)
    ordering = ("-id",)