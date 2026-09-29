from django.core.management.base import BaseCommand
from tqdm import tqdm

from annotations.models import Collection
from belege.models import Beleg


class Command(BaseCommand):
    help = "links collections to belege"

    def handle(self, *args, **options):
        Collection.objects.filter(es_document__isnull=True).delete()
        queryset = Collection.objects.filter(beleg__isnull=True).distinct()
        total = queryset.count()

        for x in tqdm(queryset.iterator(chunk_size=200), total=total):
            es_docs = list(x.es_document.values_list("es_id", flat=True))
            # only fetch pks, not full Beleg rows (they carry large xml fields)
            beleg_pks = Beleg.objects.filter(dboe_id__in=es_docs).values_list(
                "pk", flat=True
            )
            x.beleg.set(beleg_pks)
