from typing import Dict, Any
from django.utils import timezone
from games.models import Game, PriceHistory, PriceAlert
from games.services.itad import sync_game_prices


def sync_all_tracked_games() -> Dict[str, int]:
    """
    Batch utility designed to run via management command or cron/celery.
    Syncs live prices for games in backlogs or active price alerts.
    """
    tracked_game_ids = set(
        Game.objects.filter(ownerships__isnull=False).values_list('id', flat=True)
    ) | set(
        Game.objects.filter(price_alerts__is_active=True).values_list('id', flat=True)
    )

    games = Game.objects.filter(id__in=tracked_game_ids)
    synced_count = 0
    alerts_triggered = 0

    for game in games:
        old_price = game.current_best_price
        updated_game = sync_game_prices(game)
        synced_count += 1

        # Record PriceHistory snapshot if current_best_price changed
        if updated_game.current_best_price and updated_game.current_best_price != old_price:
            PriceHistory.objects.create(
                game=updated_game,
                store_name=updated_game.current_best_store or "Unknown",
                price=updated_game.current_best_price,
                regular_price=updated_game.current_best_price,  # Updated on next full payload
                cut_percentage=0
            )

        # Check PriceAlerts
        if updated_game.current_best_price:
            alerts = PriceAlert.objects.filter(
                game=updated_game,
                is_active=True,
                target_price__gte=updated_game.current_best_price
            )
            for alert in alerts:
                if not alert.preferred_store or alert.preferred_store.lower() == (updated_game.current_best_store or "").lower():
                    alert.triggered_at = timezone.now()
                    alert.is_active = False
                    alert.save()
                    alerts_triggered += 1

    return {"synced": synced_count, "alerts_triggered": alerts_triggered}