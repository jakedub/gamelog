import strawberry
import strawberry_django
from typing import List, Optional
from games.models import Game, GameOwnership, PriceAlert, PriceHistory
from games.services.search import search_itad_games
from .types import DealType, GameSearchResultType, GameType, GameOwnershipType, PriceAlertType, PriceHistoryType

@strawberry.type
class Query:
    @strawberry.field
    def search_games(self, query: str, limit: Optional[int] = 10) -> List[GameSearchResultType]:
            if not query or not query.strip():
                return []

            raw_results = search_itad_games(query=query.strip(), limit=limit or 10)

            results = []
            for item in raw_results:
                deals = [
                    DealType(
                        shop_name=d["shop_name"],
                        price=d["price"],
                        regular_price=d["regular_price"],
                        cut=d["cut"],
                        url=d["url"],
                    )
                    for d in item.get("deals", [])
                ]

                results.append(
                    GameSearchResultType(
                        id=item["itad_id"],
                        itad_id=item["itad_id"],
                        title=item["title"],
                        slug=item["slug"],
                        current_best_price=item["current_best_price"],
                        current_best_store=item["current_best_store"],
                        historical_low=item["historical_low"],
                        deal_url=item["deal_url"],
                        deals=deals,
                    )
                )

            return results
    @strawberry.field
    def games(self, title: Optional[str] = None) -> List[GameType]:
        queryset = Game.objects.all().prefetch_related('genres', 'tags', 'ownerships')
        if title:
            queryset = queryset.filter(title__icontains=title)
        return queryset

    @strawberry.field
    def game(self, id: int) -> Optional[GameType]:
        return Game.objects.filter(id=id).first()

    @strawberry.field
    def ownerships(self, platform: Optional[str] = None) -> List[GameOwnershipType]:
        queryset = GameOwnership.objects.select_related('game').all()
        if platform:
            queryset = queryset.filter(platform=platform)
        return queryset

    @strawberry.field
    def price_alerts(self, is_active: bool = True) -> List[PriceAlertType]:
        return PriceAlert.objects.filter(is_active=is_active).select_related('game')

    @strawberry.field
    def price_history(self, game_id: int) -> List[PriceHistoryType]:
        return PriceHistory.objects.filter(game_id=game_id).select_related('game')