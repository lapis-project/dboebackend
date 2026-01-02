from django.core.management.base import BaseCommand
from tqdm import tqdm

from annotations.models import Collection
from belege.models import Beleg


class Command(BaseCommand):
    help = "links collections to belege"

    def handle(self, *args, **options):
        items = Collection.objects.filter(es_document__isnull=True).prefetch_related(
            "es_document"
        )
        items.count()
        items.delete()
        items = Collection.objects.all()
        items.count()

        for x in tqdm(items, total=len(items)):
            es_docs = list(x.es_document.values_list("es_id", flat=True))
            belege = Beleg.objects.filter(dboe_id__in=es_docs)
            x.beleg.set(belege)
