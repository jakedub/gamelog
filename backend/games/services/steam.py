import requests
from typing import List, Dict, Any, Optional
from django.conf import settings

def get_api_key() -> str:
    return getattr(settings, "STEAM_API_KEY", "")


def fetch_user_steam_library(steam_id: str) -> List[Dict[str, Any]]:
    """
    Fetches all owned games for a given Steam 64-bit ID.
    Returns raw list of games with appid, play_time, name, and icon hash.
    """
    api_key = get_api_key()

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
            data = response.json()
            return data.get("response", {}).get("games", [])
    except requests.RequestException:
        pass

    return []


def get_steam_banner_url(app_id: int) -> str:
    """Returns official Steam CDN header image URL for a given AppID."""
    return f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/header.jpg"