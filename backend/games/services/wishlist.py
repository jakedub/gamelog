from datetime import datetime, timezone
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from games.models import Game, WishlistItem
from games.services.itad import reconcile_steam_appids_with_itad, sync_game_prices


def fetch_steam_app_details(app_id: str) -> dict:
    """
    Fetches game metadata (title, header image) from the Steam Store API.
    """
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json().get(str(app_id), {})
            if data.get("success"):
                game_data = data.get("data", {})
                return {
                    "title": game_data.get("name"),
                    "boxart_url": game_data.get("header_image"),
                }
    except (requests.RequestException, ValueError):
        pass

    return {}


def fetch_steam_wishlist(steam_id: str = None) -> list:
    """
    Fetches Steam wishlist items via the IWishlistService Web API.
    """
    steam_id = steam_id or getattr(settings, "STEAM_ID", "")
    if not steam_id:
        return []

    url = f"https://api.steampowered.com/IWishlistService/GetWishlist/v1/?steamid={steam_id}"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return data.get("response", {}).get("items", [])
    except (requests.RequestException, ValueError):
        pass

    return []


def fetch_itad_waitlist() -> list:
    """
    Fetches ITAD Waitlist items using API Key or OAuth User Access Token.
    """
    token = getattr(settings, "ITAD_OAUTH_TOKEN", "") or getattr(
        settings, "ITAD_API_KEY", ""
    )
    if not token:
        return []

    url = f"https://api.isthereanydeal.com/user/waitlist/v2?key={token}"
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, dict):
                return data.get("list", [])
            elif isinstance(data, list):
                return data
    except (requests.RequestException, ValueError):
        pass

    return []


def sync_user_wishlist(user=None) -> None:
    """
    Synchronizes Steam Wishlist and ITAD Waitlist items into WishlistItem records.
    Hydrates missing game titles directly from the Steam Store API.
    """
    if not user:
        User = get_user_model()
        user = User.objects.first()

    if not user:
        return

    # --- 1. Process Steam Wishlist ---
    steam_items = fetch_steam_wishlist()
    steam_appids = [str(item["appid"]) for item in steam_items if "appid" in item]

    # Batch resolve ITAD UUIDs for all Steam AppIDs
    itad_map = reconcile_steam_appids_with_itad(steam_appids)

    for item in steam_items:
        app_id = str(item.get("appid"))
        if not app_id:
            continue

        itad_id = itad_map.get(app_id)

        # Get existing or create new Game record
        game = Game.objects.filter(steam_appid=app_id).first()

        if not game or game.title.startswith("Steam Game ") or not game.boxart_url:
                    details = fetch_steam_app_details(app_id)
                    title = details.get("title") or f"Steam Game {app_id}"
                    boxart_url = details.get("boxart_url")

                    if not game:
                        game = Game.objects.create(
                            steam_appid=app_id,
                            title=title,
                            boxart_url=boxart_url,
                            itad_id=itad_id,
                        )
                    else:
                        game.title = title
                        if boxart_url:
                            game.boxart_url = boxart_url
                        game.save()

        # Backfill ITAD ID if resolved after creation
        if not game.itad_id and itad_id:
            game.itad_id = itad_id
            game.save()

        # Parse unix timestamp into timezone-aware datetime
        raw_date = item.get("date_added")
        added_at = (
            datetime.fromtimestamp(raw_date, tz=timezone.utc)
            if raw_date
            else None
        )

        # Sync ITAD pricing analytics if UUID exists
        if game.itad_id:
            sync_game_prices(game)

        # Upsert WishlistItem
        wishlist_item, _ = WishlistItem.objects.get_or_create(
            user=user, game=game
        )
        wishlist_item.steam_priority = item.get("priority", 0)
        wishlist_item.added_to_wishlist_at = added_at
        wishlist_item.source = (
            "BOTH" if wishlist_item.source in ["ITAD", "BOTH"] else "STEAM"
        )
        wishlist_item.save()

    # --- 2. Process ITAD Waitlist ---
    itad_items = fetch_itad_waitlist()
    for item in itad_items:
        itad_id = item.get("id")
        title = item.get("title", "ITAD Game")

        if not itad_id:
            continue

        game = Game.objects.filter(itad_id=itad_id).first()
        if not game:
            game = Game.objects.create(itad_id=itad_id, title=title)

        sync_game_prices(game)

        wishlist_item, _ = WishlistItem.objects.get_or_create(
            user=user, game=game
        )
        wishlist_item.itad_price_cap = item.get("price", {}).get("amount")
        wishlist_item.itad_price_cut = item.get("cut")
        wishlist_item.source = (
            "BOTH" if wishlist_item.source in ["STEAM", "BOTH"] else "ITAD"
        )
        wishlist_item.save()