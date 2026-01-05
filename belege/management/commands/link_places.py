from django.core.management.base import BaseCommand
from tqdm import tqdm

from belege.models import (
    Beleg,
)
from siglen.models import BelegSigle, Sigle

namespaces = {"tei": "http://www.tei-c.org/ns/1.0"}


class Command(BaseCommand):
    help = "Links Belege to Siglen"

    def handle(self, *args, **options):
        total = Beleg.objects.count()
        for item in tqdm(Beleg.objects.iterator(), total=total):
            try:
                try:
                    doc = item.orig_xml
                except Exception as e:
                    print(f"failed to parse {item.dboe_id} due to {e}")
                    continue

                for x in doc.xpath(".//tei:usg[@type='geo']", namespaces=namespaces):
                    try:
                        corresp = x.attrib["corresp"]
                    except KeyError:
                        corresp = None
                    orig_names = x.xpath(
                        ".//tei:placeName[@type='orig']/text()", namespaces=namespaces
                    )
                    try:
                        sigle_str = (
                            x.xpath(".//tei:listPlace/@corresp", namespaces=namespaces)[
                                0
                            ]
                            .split("sigle:")[-1]
                            .strip()
                        )
                    except IndexError:
                        continue
                    sigle_name = x.xpath(
                        ".//tei:placeName/text()", namespaces=namespaces
                    )[-1]
                    try:
                        sigle = Sigle.objects.get(sigle=sigle_str)
                    except Sigle.DoesNotExist:
                        sigle, _ = Sigle.objects.get_or_create(
                            sigle=sigle_str, name=sigle_name, kind="ort"
                        )
                        print(f"created {sigle}")
                    if orig_names is not None:
                        sigle.orig_names = sigle.orig_names + orig_names
                        sigle.save()
                    BelegSigle.objects.get_or_create(
                        beleg=item, sigle=sigle, corresp=corresp
                    )
            except Exception as e:
                print(f"failed to process {item} due to {e}")
        print("done")
