from typing import List, Dict, Any
import requests
from django.conf import settings
from django.utils.text import slugify


def search_itad_games(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    api_key = getattr(settings, "ITAD_API_KEY", "")
    if not api_key or not query.strip():
        return []

    url = "https://api.isthereanydeal.com/games/search/v1"
    params = {"key": api_key, "title": query, "limit": limit}

    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code != 200:
            return []

        results = res.json()
        search_results = []

        for item in results:
            deals_list = []
            best_price = None
            best_store = None
            deal_url = None

            # Extract deals array if present
            raw_deals = item.get("deals", [])
            if raw_deals:
                top_deal = raw_deals[0]
                best_price = top_deal.get("price", {}).get("amount")
                best_store = top_deal.get("shop", {}).get("name")
                deal_url = top_deal.get("url")

                for d in raw_deals:
                    deals_list.append({
                        "shop_name": d.get("shop", {}).get("name", "Unknown"),
                        "price": d.get("price", {}).get("amount", 0.0),
                        "regular_price": d.get("regular", {}).get("amount", 0.0),
                        "cut": d.get("cut", 0),
                        "url": d.get("url", ""),
                    })

            # Historical low
            history_low = item.get("historyLow", {}).get("amount")

            assets = item.get("assets") or {}
            boxart_url = assets.get("boxart")
            # Pick a high-res banner option with fallback
            banner_url = (
                assets.get("banner600")
                or assets.get("banner400")
                or assets.get("banner300")
                or assets.get("banner145")
            )

            search_results.append({
                "itad_id": item["id"],
                "title": item["title"],
                "slug": item.get("slug") or slugify(item["title"]),
                "boxart_url": boxart_url,
                "banner_url": banner_url,
                "current_best_price": best_price,
                "current_best_store": best_store,
                "historical_low": history_low,
                "deal_url": deal_url,
                "deals": deals_list,
            })

        return search_results

    except requests.RequestException:
        return []