from django.core.management.base import BaseCommand
from django.db import transaction

from backend.models import (
    Player,
    Leaderboard,
    LeaderboardEntry,
    KillsStats,
    MiningStats,
    FarmingStats,
    TravellingStats,
)


class Command(BaseCommand):
    help = "Clear all leaderboard/stat data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--players",
            action="store_true",
            help="Also delete all players",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        include_players = options["players"]

        counts = {
            "leaderboards": Leaderboard.objects.count(),
            "entries": LeaderboardEntry.objects.count(),
            "kills": KillsStats.objects.count(),
            "mining": MiningStats.objects.count(),
            "farming": FarmingStats.objects.count(),
            "travelling": TravellingStats.objects.count(),
            "players": Player.objects.count(),
        }

        Leaderboard.objects.all().delete()

        if include_players:
            Player.objects.all().delete()

        self.stdout.write(self.style.SUCCESS("Leaderboard/stat data cleared."))
        self.stdout.write(f"Leaderboards deleted: {counts['leaderboards']}")
        self.stdout.write(f"Entries deleted: {counts['entries']}")
        self.stdout.write(f"Kills stats deleted: {counts['kills']}")
        self.stdout.write(f"Mining stats deleted: {counts['mining']}")
        self.stdout.write(f"Farming stats deleted: {counts['farming']}")
        self.stdout.write(f"Travelling stats deleted: {counts['travelling']}")

        if include_players:
            self.stdout.write(f"Players deleted: {counts['players']}")
        else:
            self.stdout.write(
                "Players were kept. Use --players to clear them as well."
            )
