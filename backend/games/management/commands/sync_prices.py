from django.core.management.base import BaseCommand
from games.services.deals_sync import sync_all_tracked_games


class Command(BaseCommand):
    help = "Syncs live ITAD prices and checks price alerts for all tracked games in backlogs/wishlists."

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Print detailed execution output',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting ITAD price synchronization..."))

        try:
            stats = sync_all_tracked_games()
            
            synced_count = stats.get("synced", 0)
            alerts_count = stats.get("alerts_triggered", 0)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully synced {synced_count} game(s). "
                    f"Triggered {alerts_count} price alert(s)."
                )
            )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to sync prices: {str(e)}"))