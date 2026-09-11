from django.contrib import admin
from django.utils.html import format_html
from games.models.catalog import Genre, Tag, Game
from games.models.deals import PriceAlert, PriceHistory
from games.models.ownership import GameOwnership


# Register your models here.
@admin.register(Genre)
class CatalogAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]

@admin.register(Tag)
class CatalogAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "source"]

@admin.register(Game)
class CatalogAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "banner_url", "current_best_price", "current_best_store",
                    "historical_low_price", "historical_low_store", "last_price_sync"]