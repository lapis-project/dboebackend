from django.core.management.base import BaseCommand
from tqdm import tqdm

from annotations.models import Tag
from belege.models import Beleg


class Command(BaseCommand):
    help = "links tags to belege"

    def handle(self, *args, **options):
        items = Tag.objects.filter(es_documents__isnull=True)
        items.delete()
        items = Tag.objects.all()
        items.count()

        for x in tqdm(items, total=len(items)):
            es_docs = list(x.es_documents.values_list("es_id", flat=True))
            belege = Beleg.objects.filter(dboe_id__in=es_docs)
            x.belege.set(belege)
