from django.core.management.base import BaseCommand
from django.db import connection, transaction

from belege.models import Beleg


class Command(BaseCommand):
    help = "deletes all Beleg objects"

    def handle(self, *args, **options):
        confirmation = input(
            "This will delete all Belege and related objects. "
            "Are you sure? If so, please type YES! "
        )
        if confirmation != "YES":
            self.stdout.write("Deletion cancelled.")
            return

        table_name = connection.ops.quote_name(Beleg._meta.db_table)
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(f"TRUNCATE TABLE {table_name} CASCADE")

        self.stdout.write(
            self.style.SUCCESS(
                f"Truncated {Beleg._meta.db_table} and all related tables"
            )
        )
