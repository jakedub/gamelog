from typing import List, Optional
from django.db import models
import strawberry
import strawberry_django
from strawberry import auto

from games.models import Game, GameOwnership, Genre, PriceAlert, PriceHistory, Tag, WishlistItem


@strawberry_django.type(Genre)
class GenreType:
    id: auto
    name: auto
    slug: auto


@strawberry_django.type(Tag)
class TagType:
    id: auto
    name: auto
    slug: auto
    source: auto


@strawberry_django.type(PriceHistory)
class PriceHistoryType:
    id: auto
    game: "GameType"
    store_name: auto
    price: auto
    regular_price: auto
    cut_percentage: auto
    recorded_at: auto


@strawberry_django.type(Game)
class GameType:
    id: auto
    itad_id: auto
    title: auto
    slug: auto
    banner_url: auto
    current_best_store: auto
    historical_low_price: auto
    historical_low_store: auto
    deal_url: Optional[str]
    last_price_sync: auto
    steam_appid: Optional[str] = None
    boxart_url: Optional[str] = None
    genres: List[GenreType]
    tags: List[TagType]
    ownerships: List["GameOwnershipType"]

    @strawberry.field
    def current_best_price(self, root: Game) -> float | None:
        if root.current_best_price is not None:
            return float(root.current_best_price)
        return None

    @strawberry.field
    def price_history(self, root: Game) -> List[PriceHistoryType]:
        return root.price_history.all()[:10]


@strawberry_django.type(GameOwnership)
class GameOwnershipType:
    id: auto
    game: GameType
    status: auto
    platform: str
    access_type: auto
    user_rating: auto
    notes: auto
    created_at: auto
    updated_at: auto


@strawberry_django.type(PriceAlert)
class PriceAlertType:
    id: auto
    game: GameType
    target_price: auto
    preferred_store: auto
    is_active: auto
    triggered_at: auto


@strawberry.type
class DealType:
    shop_name: str
    price: float
    regular_price: float
    cut: int
    url: str


@strawberry.type
class GameSearchResultType:
    id: str
    itad_id: str
    title: str
    slug: str
    boxart_url: Optional[str] = None
    banner_url: Optional[str] = None
    current_best_price: Optional[float] = None
    current_best_store: Optional[str] = None
    historical_low: Optional[float] = None
    deal_url: Optional[str] = None
    deals: Optional[List[DealType]] = None


@strawberry_django.type(WishlistItem)
class WishlistItemType:
    id: strawberry.ID
    source: str
    itad_price_cut: Optional[int]
    itad_price_cap: Optional[float]
    steam_priority: int
    added_to_wishlist_at: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    game: GameType

    @strawberry.field
    def target_price(self, root: WishlistItem) -> float | None:
        if getattr(root, "target_price", None) is not None:
            return float(root.target_price)
        return None

    @strawberry.field
    def is_below_target(self, root: WishlistItem) -> bool:
        return getattr(root, "is_on_sale_below_target", False)