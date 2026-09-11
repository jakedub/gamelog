import requests
from typing import List, Dict, Any, Optional
from django.conf import settings
from django.utils.text import slugify
from games.models import Game, GameOwnership
from games.services.itad import reconcile_steam_appids_with_itad


def get_steam_banner_url(app_id: str) -> str:
    return f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/header.jpg"


def fetch_user_steam_library(steam_id: str) -> List[Dict[str, Any]]:
    api_key = getattr(settings, "STEAM_API_KEY", "")
    steam_id = getattr(settings, "STEAM_ID", "")
    
    if not api_key or not steam_id:
        return []

    url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
    params = {
        "key": api_key,
        "steamid": steam_id,
        "include_appinfo": True,
        "include_played_free_games": True,
        "format": "json",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json().get("response", {}).get("games", [])
    except requests.RequestException:
        pass

    return []


def import_steam_games_for_user(steam_id: str, user) -> List[GameOwnership]:
    raw_games = fetch_user_steam_library(steam_id)
    if not raw_games:
        return []

    # 1. Extract AppIDs and batch resolve missing ITAD UUIDs
    app_ids = [str(raw["appid"]) for raw in raw_games if "appid" in raw]
    unmapped_app_ids = list(
        Game.objects.filter(steam_appid__in=app_ids, itad_id__isnull=True)
        .values_list("steam_appid", flat=True)
    )
    # Add app_ids not yet in the DB at all
    existing_app_ids = set(Game.objects.filter(steam_appid__in=app_ids).values_list("steam_appid", flat=True))
    new_app_ids = [aid for aid in app_ids if aid not in existing_app_ids]
    
    # Bulk reconcile with ITAD lookup API
    itad_map = reconcile_steam_appids_with_itad(list(set(unmapped_app_ids + new_app_ids)))

    ownership_records = []

    for raw in raw_games:
        app_id = str(raw.get("appid"))
        title = raw.get("name", f"Steam App {app_id}")
        itad_id = itad_map.get(app_id)

        # 2. Get or update local Game entry
        game, created = Game.objects.get_or_create(
            steam_appid=app_id,
            defaults={
                "title": title,
                "slug": slugify(title),
                "boxart_url": get_steam_banner_url(app_id),
                "itad_id": itad_id,
            }
        )

        # Update itad_id or boxart if newly discovered
        updated = False
        if not game.itad_id and itad_id:
            game.itad_id = itad_id
            updated = True
        if not game.boxart_url:
            game.boxart_url = get_steam_banner_url(app_id)
            updated = True
            
        if updated:
            game.save()

        # 3. Attach ownership
        ownership, _ = GameOwnership.objects.update_or_create(
            game=game,
            defaults={
                "platform": "Steam"
            }
        )
        ownership_records.append(ownership)

    return ownership_records