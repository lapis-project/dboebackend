import os

from acdh_tei_pyutils.tei import TeiReader
from acdh_tei_pyutils.utils import get_xmlid
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.management.base import BaseCommand

from belege.models import Beleg, DboeXmlFile
from siglen.models import BelegSigle, Sigle


class Command(BaseCommand):
    help = "links Belege with Siglen"

    def add_arguments(self, parser):
        parser.add_argument(
            "--starts_with",
            type=str,
            default=None,
            help="only import files whose dboe_id starts with this value",
        )

    def handle(self, *args, **options):
        namespaces = {"tei": "http://www.tei-c.org/ns/1.0"}
        failed_path = os.path.join(os.getcwd(), "failed.txt")
        with open(failed_path, "w", encoding="utf-8"):
            pass

        files = DboeXmlFile.objects.filter(belege_linked=False)
        starts_with = options.get("starts_with")
        if starts_with:
            files = files.filter(dboe_id__startswith=starts_with)
        print(f"importing data from {files.count()} files")
        for f, file in enumerate(files, start=1):
            print(f"{f}/{len(files)} files")
            doc = TeiReader(file.get_url_to_file())
            for doc in doc.any_xpath(".//tei:entry[@xml:id]"):
                xml_id = get_xmlid(doc)
                try:
                    beleg = Beleg.objects.get(dboe_id=xml_id)
                except ObjectDoesNotExist:
                    print(f"Beleg with id {xml_id} does not exist")
                    continue
                sigle_cache = {}

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
                            try:
                                BelegSigle.objects.get_or_create(
                                    beleg=beleg, sigle=sigle, corresp=corresp
                                )
                            except MultipleObjectsReturned:
                                continue
            file.belege_linked = True
            file.save()
            print(f"done with {file}")
