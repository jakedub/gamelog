from decimal import Decimal

import requests
from typing import List, Dict, Optional
from django.conf import settings
from django.utils import timezone
from games.models.deals import PriceHistory
from games.models import Game


def get_itad_api_key() -> str:
    return getattr(settings, "ITAD_API_KEY", "")


def reconcile_steam_appids_with_itad(steam_appids: list[str]) -> dict[str, str]:
    """
    Maps Steam AppIDs to ITAD Game UUIDs using ITAD's Lookup v1 API.
    Returns: {"1373090": "018d937f-..."}
    """
    key = getattr(settings, "ITAD_API_KEY", "")
    if not key or not steam_appids:
        return {}

    mapping = {}
    
    # Query ITAD per AppID or batch via parameters
    for app_id in steam_appids:
        url = f"https://api.isthereanydeal.com/games/lookup/v1?key={key}&shop=steam&appid={app_id}"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                # ITAD returns {"game": {"id": "UUID", "title": "..."}} or {"id": "UUID"}
                game_info = data.get("game", {})
                itad_id = game_info.get("id") or data.get("id")
                if itad_id:
                    mapping[app_id] = itad_id
        except (requests.RequestException, ValueError):
            continue

    return mapping

def sync_game_prices(game) -> None:
    """
    Syncs current best price, store name, and deal URL for a Game model using ITAD v2 API.
    """
    key = getattr(settings, "ITAD_API_KEY", "")
    if not key or not game.itad_id:
        return

    # Ensure UUID is formatted as a clean lowercase string
    itad_id_str = str(game.itad_id).lower()

    url = f"https://api.isthereanydeal.com/games/prices/v2?key={key}"
    headers = {"Content-Type": "application/json"}
    payload = [itad_id_str]

    try:
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            for entry in data:
                # Cast both sides to string to avoid UUID vs str comparison failure
                if str(entry.get("id")).lower() == itad_id_str:
                    deals = entry.get("deals", [])
                    if deals:
                        # Find the deal with the lowest price amount
                        best_deal = min(
                            deals,
                            key=lambda d: d.get("price", {}).get("amount", float("inf")),
                            default=None,
                        )
                        if best_deal and "price" in best_deal:
                            game.current_best_price = Decimal(str(best_deal["price"]["amount"]))
                            game.current_best_store = best_deal.get("shop", {}).get("name")
                            game.deal_url = best_deal.get("url")
                            game.save(update_fields=["current_best_price", "current_best_store", "deal_url"])
                            return

            # Clear out prices if game has no current deals listed
            game.current_best_price = None
            game.current_best_store = None
            game.deal_url = None
            game.save(update_fields=["current_best_price", "current_best_store", "deal_url"])

    except (requests.RequestException, ValueError, KeyError):
        pass

def batch_sync_itad_prices():
    games = Game.objects.exclude(itad_id__isnull=True).exclude(itad_id="")
    if not games.exists():
        return 0

    itad_map = {game.itad_id: game for game in games}
    itad_uuids = list(itad_map.keys())

    url = f"https://api.isthereanydeal.com/games/prices/v3?key={settings.ITAD_API_KEY}"
    response = requests.post(url, json=itad_uuids, timeout=10)

    if response.status_code != 200:
        return 0

    data = response.json()
    games_to_update = []
    history_to_create = []

    for entry in data:
        itad_id = entry.get("id")
        game = itad_map.get(itad_id)
        if not game or not entry.get("deals"):
            continue

        best_deal = min(entry["deals"], key=lambda d: d["price"]["amount"])
        new_price = best_deal["price"]["amount"]
        new_store = best_deal["shop"]["name"]
        new_url = best_deal["url"]

        # Only create history entry if the price or store actually shifted
        if (
            game.current_best_price != new_price
            or game.current_best_store != new_store
        ):
            history_to_create.append(
                PriceHistory(game=game, price=new_price, store=new_store)
            )

        game.current_best_price = new_price
        game.current_best_store = new_store
        game.deal_url = new_url
        games_to_update.append(game)

    with transaction.atomic():
        if games_to_update:
            Game.objects.bulk_update(
                games_to_update,
                ["current_best_price", "current_best_store", "deal_url"],
            )
        if history_to_create:
            PriceHistory.objects.bulk_create(history_to_create)

    return len(games_to_update)