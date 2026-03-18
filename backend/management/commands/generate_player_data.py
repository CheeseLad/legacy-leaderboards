from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
import random

from backend.models import (
    Player,
    Leaderboard,
    LeaderboardEntry,
    KillsStats,
    MiningStats,
    FarmingStats,
    TravellingStats,
    StatsType,
    DifficultyType,
)


class Command(BaseCommand):
    help = "Generate fake leaderboard/stat data for an existing player by UUID"

    def add_arguments(self, parser):
        parser.add_argument(
            "--uuid",
            required=True,
            help="Existing player UUID (stored in Player.uid)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        uid = options["uuid"]

        try:
            player = Player.objects.get(uid=uid)
        except Player.DoesNotExist as exc:
            new_player = Player.objects.create(uid=uid, name=f"Player {uid}")
            self.stdout.write(self.style.WARNING(
                f"Player with uuid '{uid}' was not found. Created new player with name '{new_player.name}'."
            ))
            player = new_player

        self.stdout.write(f"Generating data for player '{player.name}' ({player.uid})...")

        leaderboards = []
        for stats_type in StatsType:
            for difficulty in DifficultyType:
                leaderboard, _ = Leaderboard.objects.get_or_create(
                    stats_type=stats_type,
                    difficulty=difficulty,
                )
                leaderboards.append((stats_type, leaderboard))

        for stats_type, leaderboard in leaderboards:
            score = random.randint(0, 1000)

            entry, created = LeaderboardEntry.objects.update_or_create(
                player=player,
                leaderboard=leaderboard,
                defaults={
                    "total_score": score,
                    "rank": 0,
                },
            )

            if stats_type == StatsType.KILLS:
                KillsStats.objects.update_or_create(
                    entry=entry,
                    defaults={
                        "zombie": random.randint(0, 100),
                        "skeleton": random.randint(0, 100),
                        "creeper": random.randint(0, 100),
                        "spider": random.randint(0, 100),
                        "spider_jockey": random.randint(0, 50),
                        "zombie_pigman": random.randint(0, 50),
                        "slime": random.randint(0, 50),
                    },
                )

            elif stats_type == StatsType.MINING:
                MiningStats.objects.update_or_create(
                    entry=entry,
                    defaults={
                        "dirt": random.randint(0, 200),
                        "stone": random.randint(0, 200),
                        "sand": random.randint(0, 200),
                        "cobblestone": random.randint(0, 200),
                        "gravel": random.randint(0, 200),
                        "clay": random.randint(0, 200),
                        "obsidian": random.randint(0, 50),
                    },
                )

            elif stats_type == StatsType.FARMING:
                FarmingStats.objects.update_or_create(
                    entry=entry,
                    defaults={
                        "eggs": random.randint(0, 100),
                        "wheat": random.randint(0, 100),
                        "mushroom": random.randint(0, 100),
                        "sugarcane": random.randint(0, 100),
                        "milk": random.randint(0, 100),
                        "pumpkin": random.randint(0, 100),
                    },
                )

            elif stats_type == StatsType.TRAVELLING:
                TravellingStats.objects.update_or_create(
                    entry=entry,
                    defaults={
                        "walked": random.randint(0, 10000),
                        "fallen": random.randint(0, 1000),
                        "minecart": random.randint(0, 5000),
                        "boat": random.randint(0, 5000),
                    },
                )

            action = "Created" if created else "Updated"
            self.stdout.write(
                f"{action} entry for {stats_type.label} / {leaderboard.get_difficulty_display()}"
            )

        self.stdout.write("Recalculating ranks...")

        for _, leaderboard in leaderboards:
            entries = LeaderboardEntry.objects.filter(
                leaderboard=leaderboard
            ).order_by("-total_score")

            for rank, entry in enumerate(entries, start=1):
                if entry.rank != rank:
                    entry.rank = rank
                    entry.save(update_fields=["rank"])

        self.stdout.write(self.style.SUCCESS("Done generating player data."))
