import xml.etree.ElementTree as ET

from acdh_tei_pyutils.tei import TeiReader
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
                    doc = TeiReader(ET.tostring(item.orig_xml).decode("utf-8"))
                except Exception as e:
                    print(f"failed to process {item.id} due to {e}")
                    continue

                for x in doc.any_xpath(".//tei:usg"):
                    try:
                        corresp = x.attrib["corresp"]
                    except KeyError:
                        corresp = None
                    try:
                        y = x.xpath(".//tei:place", namespaces=namespaces)[-1]
                    except IndexError:
                        continue
                    try:
                        idno = y.xpath("./tei:idno/text()", namespaces=namespaces)[0]
                        placename = y.xpath(
                            "./tei:placename/text()", namespaces=namespaces
                        )[0]
                    except IndexError:
                        continue
                    try:
                        sigle = Sigle.objects.get(sigle=idno)
                    except Sigle.DoesNotExist:
                        sigle, _ = Sigle.objects.get_or_create(
                            sigle=idno, name=placename, kind="ort"
                        )
                    BelegSigle.objects.get_or_create(
                        beleg=item, sigle=sigle, corresp=corresp
                    )
            except Exception as e:
                print(f"failed to process {item} due to {e}")
        print("done")
