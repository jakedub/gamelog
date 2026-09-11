import strawberry
from strawberry.types import Info
from typing import Optional, List
from games.services.wishlist import sync_user_wishlist
from games.services.steam import import_steam_games_for_user
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
@strawberry.type
class Mutation:
    @strawberry.mutation
    def import_steam_library(self, info: Info, steam_id: str) -> List[GameOwnershipType]:
        user = info.context.request.user
        
        if not user or user.is_anonymous:
            raise Exception("Authentication required to import Steam library.")

        return import_steam_games_for_user(steam_id=steam_id, user=user)
@strawberry.type
class Mutation:
    @strawberry.mutation
    def sync_wishlist(self, info: Info) -> bool:
        """
        Ingests Steam Wishlist & ITAD Waitlist items into the database.
        """
        user = info.context.request.user
        
        # Single-user fallback if running unauthenticated in dev
        if not user.is_authenticated:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.first()

        if not user:
            raise Exception("No user found to assign wishlist items to.")

        sync_user_wishlist(user)
        return True