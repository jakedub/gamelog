import requests
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from games.models import Game

def get_api_key() -> str:
    return getattr(settings, "ITAD_API_KEY", "")


def sync_game_prices(game: Game) -> Game:
    """
    Resolves ITAD ID for a game if missing, then updates current best deal 
    and historical low price directly on the Game model.
    """
    api_key = get_api_key
    if not api_key:
        return game

    # 1. Resolve ITAD ID if missing
    if not game.itad_id:
        lookup_url = "https://api.isthereanydeal.com/games/lookup/v1"
        res = requests.get(lookup_url, params={"key": api_key, "title": game.title})
        if res.status_code == 200:
            data = res.json()
            if data.get("found"):
                game.itad_id = data["game"]["id"]

    if not game.itad_id:
        return game

    prices_url = f"https://api.isthereanydeal.com/games/prices/v2?key={api_key}"
    payload = [game.itad_id]

    res = requests.post(prices_url, json=payload)
    if res.status_code == 200:
        results = res.json()
        if results and len(results) > 0:
            game_data = results[0]
            deals = game_data.get("deals", [])

            # Find current best deal (lowest price among active store deals)
            if deals:
                best_deal = min(deals, key=lambda d: d["price"]["amount"])
                game.current_best_price = Decimal(str(best_deal["price"]["amount"]))
                game.current_best_store = best_deal["shop"]["name"]

            # Process historical low if provided by ITAD endpoint
            history_low = game_data.get("historyLow")
            if history_low:
                game.historical_low_price = Decimal(str(history_low["price"]["amount"]))
                game.historical_low_store = history_low.get("shop", {}).get("name", "")

            game.last_price_sync = timezone.now()
            game.save()

    return game