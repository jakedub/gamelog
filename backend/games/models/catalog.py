from django.db import models
from django.utils.text import slugify
from django.conf import settings


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    source = models.CharField(max_length=50, default="Steam")

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.source})"


class Game(models.Model):
    # Primary Cross-Platform Identifiers
    itad_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="IsThereAnyDeal Game UUID",
    )
    steam_appid = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="Steam Store AppID",
    )

    # Core Metadata
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, db_index=True)
    boxart_url = models.URLField(max_length=1024, null=True, blank=True)
    banner_url = models.URLField(max_length=1024, null=True, blank=True)

    # Categorization Relationships
    genres = models.ManyToManyField(Genre, blank=True, related_name="games")
    tags = models.ManyToManyField(Tag, blank=True, related_name="games")

    # Cached ITAD Price Analytics
    current_best_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    current_best_store = models.CharField(max_length=100, null=True, blank=True)
    historical_low_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    historical_low_store = models.CharField(max_length=100, null=True, blank=True)
    deal_url = models.URLField(max_length=1024, null=True, blank=True)

    # Cache Control & Timestamps
    last_price_sync = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
class WishlistItem(models.Model):
    SOURCE_CHOICES = [
        ("STEAM", "Steam Wishlist"),
        ("ITAD", "ITAD Waitlist"),
        ("BOTH", "Steam & ITAD"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlist_items",
    )
    game = models.ForeignKey(
        "games.Game", on_delete=models.CASCADE, related_name="wishlisted_by"
    )

    # Track origin
    source = models.CharField(
        max_length=10, choices=SOURCE_CHOICES, default="STEAM"
    )

    # ITAD Waitlist Specific Metadata
    itad_price_cut = models.IntegerField(
        null=True, blank=True, help_text="Target discount percentage"
    )
    itad_price_cap = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Target price cap",
    )

    # Steam Wishlist Specific Metadata
    steam_priority = models.IntegerField(
        default=0, help_text="Steam wishlist order index"
    )
    added_to_wishlist_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    target_price = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )

    class Meta:
        unique_together = ("user", "game")
        ordering = ["steam_priority", "-created_at"]

    def __str__(self):
        return f"{self.game.title} ({self.source})"
    @property
    def is_on_sale_below_target(self) -> bool:
        if self.target_price and self.game.current_best_price:
            return self.game.current_best_price <= self.target_price
        return False