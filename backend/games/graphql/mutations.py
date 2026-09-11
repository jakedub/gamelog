import strawberry
from typing import Optional
from games.services.itad import sync_game_prices
from games.models import Game, GameOwnership
from .types import GameOwnershipType, GameType
from django.utils.text import slugify

@strawberry.type
class Mutation:
    @strawberry.mutation
    def add_game_to_ownership(
        self, 
        game_id: int, 
        platform: str, 
        access_type: str = "DIGITAL", 
        status: str = "UNPLAYED",
        notes: Optional[str] = ""
    ) -> GameOwnershipType:
        game = Game.objects.get(id=game_id)
        ownership, _ = GameOwnership.objects.update_or_create(
            game=game,
            platform=platform,
            defaults={
                'access_type': access_type,
                'status': status,
                'notes': notes
            }
        )
        return ownership
    def add_game(
        self, 
        itad_id: str, 
        title: str, 
        boxart_url: Optional[str] = None
    ) -> GameType:
        slug = slugify(title)

        game, created = Game.objects.get_or_create(
            itad_id=itad_id,
            defaults={
                "title": title,
                "slug": slug,
                "boxart_url": boxart_url,
            }
        )

        # Update boxart URL if it was previously empty
        if not created and boxart_url and not game.boxart_url:
            game.boxart_url = boxart_url
            game.save(update_fields=["boxart_url"])

        sync_game_prices(game)
        return game