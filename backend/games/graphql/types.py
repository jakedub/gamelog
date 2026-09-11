import strawberry
from strawberry import auto
from typing import List, Optional
from games.models import Game, GameOwnership, PriceAlert, PriceHistory, Genre, Tag

@strawberry.django.type(Genre)
class GenreType:
    id: auto
    name: auto
    slug: auto

@strawberry.django.type(Tag)
class TagType:
    id: auto
    name: auto
    slug: auto
    source: auto

@strawberry.django.type(Game)
class GameType:
    id: auto
    itad_id: auto
    title: auto
    slug: auto
    banner_url: auto
    current_best_price: auto
    current_best_store: auto
    historical_low_price: auto
    historical_low_store: auto
    last_price_sync: auto
    genres: List[GenreType]
    tags: List[TagType]
    ownerships: List["GameOwnershipType"]

@strawberry.django.type(GameOwnership)
class GameOwnershipType:
    id: auto
    game: GameType
    status: auto
    platform: auto
    access_type: auto
    user_rating: auto
    notes: auto
    created_at: auto
    updated_at: auto

@strawberry.django.type(PriceAlert)
class PriceAlertType:
    id: auto
    game: GameType
    target_price: auto
    preferred_store: auto
    is_active: auto
    triggered_at: auto

@strawberry.django.type(PriceHistory)
class PriceHistoryType:
    id: auto
    game: GameType
    store_name: auto
    price: auto
    regular_price: auto
    cut_percentage: auto
    recorded_at: auto
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
