import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from backend.models import Achievement


def _parse_achievement(item: object, index: int) -> dict[str, object]:
    if not isinstance(item, dict):
        raise CommandError(f"Item at index {index} must be an object.")

    required_fields = ["id", "name", "description", "score"]
    missing_fields = [field for field in required_fields if field not in item]
    if missing_fields:
        missing = ", ".join(missing_fields)
        raise CommandError(f"Item at index {index} is missing required fields: {missing}")

    try:
        achievement_id = int(item["id"])
    except (TypeError, ValueError) as exc:
        raise CommandError(f"Invalid id at index {index}: {item['id']!r}") from exc

    try:
        score = int(item["score"])
    except (TypeError, ValueError) as exc:
        raise CommandError(f"Invalid score at index {index}: {item['score']!r}") from exc

    name = str(item["name"]).strip()
    description = str(item["description"]).strip()

    if not name:
        raise CommandError(f"Name cannot be blank at index {index}.")
    if not description:
        raise CommandError(f"Description cannot be blank at index {index}.")

    return {
        "id": achievement_id,
        "name": name,
        "description": description,
        "score": score,
    }


class Command(BaseCommand):
    help = "Import achievements from a JSON file into backend.Achievement"

    def add_arguments(self, parser):
        parser.add_argument(
            "input_file",
            nargs="?",
            default="./data/achievements.json",
            help="Path to input achievements JSON file",
        )
        parser.add_argument(
            "--clear-missing",
            action="store_true",
            help="Delete Achievement rows that are not present in the input file",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and report changes without writing to the database",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        file_path = Path(options["input_file"])
        clear_missing = options["clear_missing"]
        dry_run = options["dry_run"]

        if not file_path.exists():
            raise CommandError(f"Input file does not exist: {file_path}")

        try:
            raw_data = json.loads(file_path.read_text(encoding="utf-8"))
        except UnicodeDecodeError as exc:
            raise CommandError(f"Failed to decode JSON as UTF-8: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise CommandError(f"Failed to parse JSON: {exc}") from exc

        if not isinstance(raw_data, list):
            raise CommandError("Input JSON must be an array of achievement objects.")

        achievements = [_parse_achievement(item, index) for index, item in enumerate(raw_data)]

        imported_ids: set[int] = set()
        created_count = 0
        updated_count = 0
        duplicate_count = 0

        seen_ids: set[int] = set()
        for achievement in achievements:
            achievement_id = achievement["id"]
            if achievement_id in seen_ids:
                duplicate_count += 1
                continue
            seen_ids.add(achievement_id)

        for achievement in achievements:
            achievement_id = achievement["id"]
            if achievement_id in imported_ids:
                continue

            defaults = {
                "name": achievement["name"],
                "description": achievement["description"],
                "score": achievement["score"],
            }

            imported_ids.add(achievement_id)

            if dry_run:
                if Achievement.objects.filter(id=achievement_id).exists():
                    updated_count += 1
                else:
                    created_count += 1
                continue

            _, created = Achievement.objects.update_or_create(
                id=achievement_id,
                defaults=defaults,
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        deleted_count = 0
        if clear_missing and imported_ids:
            qs = Achievement.objects.exclude(id__in=imported_ids)
            deleted_count = qs.count()
            if not dry_run:
                qs.delete()

        if dry_run:
            transaction.set_rollback(True)

        self.stdout.write(
            self.style.SUCCESS(
                "Achievement import complete "
                f"(created={created_count}, updated={updated_count}, "
                f"duplicates={duplicate_count}, deleted={deleted_count}, dry_run={dry_run})."
            )
        )
