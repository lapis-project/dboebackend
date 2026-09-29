from django.core.management.base import BaseCommand
from tqdm import tqdm

from belege.models import Beleg, BelegSigle
from siglen.models import Sigle

namespaces = {"tei": "http://www.tei-c.org/ns/1.0"}


class Command(BaseCommand):
    help = "Links Belege to Siglen"

    def handle(self, *args, **options):
        queryset = Beleg.objects.exclude(
            pk__in=BelegSigle.objects.values("beleg_id")
        ).only("dboe_id", "orig_xml")
        # BelegSigle.objects.all().delete()
        sigle_cache = {}
        for item in tqdm(queryset.iterator(chunk_size=100)):
            try:
                doc = item.orig_xml
            except Exception as e:
                print(f"failed to parse {item.dboe_id} due to {e}")
                continue
            try:
                for x in doc.xpath(".//tei:usg[@type='geo']", namespaces=namespaces):
                    try:
                        corresp = x.attrib["corresp"]
                    except KeyError:
                        corresp = None

                    for full_sigle in x.xpath(
                        ".//tei:listPlace/@corresp", namespaces=namespaces
                    ):
                        if "sigle:" in full_sigle:
                            sigle_str = full_sigle.split("sigle:")[-1]

                            sigle = sigle_cache.get(sigle_str)
                            if sigle is None:
                                sigle, created = Sigle.objects.get_or_create(
                                    sigle=sigle_str,
                                )
                                if created:
                                    print(f"created {sigle}")
                                sigle_cache[sigle_str] = sigle
                            BelegSigle.objects.get_or_create(
                                beleg=item, sigle=sigle, corresp=corresp
                            )
            except:  # noqa
                print(item.dboe_id)
        print("done")
