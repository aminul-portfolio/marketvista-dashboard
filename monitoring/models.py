from django.conf import settings
from django.db import models
from django.utils import timezone


class Asset(models.Model):
    ASSET_TYPES = [
        ("crypto", "Cryptocurrency"),
        ("forex", "Forex"),
        ("index", "Index"),
        ("commodity", "Commodity"),
    ]

    symbol = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES)

    class Meta:
        ordering = ["symbol"]

    def __str__(self):
        return f"{self.symbol} ({self.get_asset_type_display()})"


class PriceSnapshot(models.Model):
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="price_snapshots",
    )
    price = models.DecimalField(max_digits=20, decimal_places=8)
    open = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    high = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    low = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    close = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    volume = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    timestamp = models.DateTimeField()

    class Meta:
        ordering = ["-timestamp"]

    def save(self, *args, **kwargs):
        if self.timestamp and timezone.is_naive(self.timestamp):
            self.timestamp = timezone.make_aware(
                self.timestamp,
                timezone.get_current_timezone(),
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.asset.symbol} @ {self.price} ({self.timestamp})"


class Alert(models.Model):
    DIRECTION = [
        ("above", "Above"),
        ("below", "Below"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="alerts",
    )
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="alerts",
    )
    target_price = models.DecimalField(max_digits=20, decimal_places=8)
    direction = models.CharField(max_length=5, choices=DIRECTION)
    is_triggered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_notified = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Alert: {self.asset.symbol} {self.direction} {self.target_price}"


class PriceOHLC(models.Model):
    SOURCE_CHOICES = [
        ("twelve", "Twelve Data"),
        ("yahoo", "Yahoo Finance"),
        ("demo_seed", "Demo Seed"),
    ]

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="ohlc_data",
    )
    timestamp = models.DateTimeField()
    open = models.DecimalField(max_digits=20, decimal_places=8)
    high = models.DecimalField(max_digits=20, decimal_places=8)
    low = models.DecimalField(max_digits=20, decimal_places=8)
    close = models.DecimalField(max_digits=20, decimal_places=8)
    volume = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="twelve")

    class Meta:
        ordering = ["-timestamp"]

    def save(self, *args, **kwargs):
        if self.timestamp and timezone.is_naive(self.timestamp):
            self.timestamp = timezone.make_aware(
                self.timestamp,
                timezone.get_current_timezone(),
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.asset.symbol} OHLC @ {self.timestamp}"


class WatchlistItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="watchlist_items",
    )
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="watchlist_items",
    )
    note = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["asset__symbol"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "asset"],
                name="unique_watchlist_item_per_user_asset",
            )
        ]

    def __str__(self):
        return f"{self.user.username} watchlist - {self.asset.symbol}"


class MarketSignal(models.Model):
    SIGNAL_TYPES = [
        ("ma_crossover", "5d/20d MA crossover"),
        ("pct_move_3d", "3-day percentage move"),
        ("volatility_spike", "Volatility spike"),
    ]

    SEVERITY_CHOICES = [
        ("INFO", "Info"),
        ("WATCHLIST", "Watchlist"),
        ("ELEVATED", "Elevated"),
    ]

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="market_signals",
    )
    signal_type = models.CharField(max_length=32, choices=SIGNAL_TYPES)
    severity = models.CharField(max_length=16, choices=SEVERITY_CHOICES)
    title = models.CharField(max_length=160)
    details = models.TextField(blank=True)
    metric_value = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
    )
    signal_timestamp = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-signal_timestamp", "-created_at"]

    def save(self, *args, **kwargs):
        if self.signal_timestamp and timezone.is_naive(self.signal_timestamp):
            self.signal_timestamp = timezone.make_aware(
                self.signal_timestamp,
                timezone.get_current_timezone(),
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.asset.symbol} - "
            f"{self.get_signal_type_display()} - "
            f"{self.severity}"
        )