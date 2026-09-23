import os

import lxml.etree as ET
from acdh_tei_pyutils.tei import TeiReader
from acdh_tei_pyutils.utils import get_xmlid
from django.core.management.base import BaseCommand
from tqdm import tqdm

from belege.models import Beleg, DboeXmlFile


class Command(BaseCommand):
    help = "imports dboe xmls"

    def add_arguments(self, parser):
        parser.add_argument(
            "--starts_with",
            type=str,
            default=None,
            help="only import files whose dboe_id starts with this value",
        )

    def handle(self, *args, **options):
        failed_path = os.path.join(os.getcwd(), "failed.txt")
        # Start with a fresh failure log for each import run.
        with open(failed_path, "w", encoding="utf-8"):
            pass

        files = DboeXmlFile.objects.filter(belege_imported=False)
        starts_with = options.get("starts_with")
        if starts_with:
            files = files.filter(dboe_id__startswith=starts_with)
        print(f"importing data from {files.count()} files")
        for f, x in enumerate(files, start=1):
            print(f"{f}/{len(files)} files")
            doc = TeiReader(x.get_url_to_file())
            fname = x.dboe_id
            items = doc.any_xpath(".//tei:entry")
            xenos = doc.any_xpath(".//tei:xenoData")
            print(f"processing {len(items)} entries from {fname}")
            for i, entry in tqdm(enumerate(items), total=len(items)):
                xml_id = get_xmlid(entry)
                node_as_text = ET.tostring(entry, encoding="unicode")
                beleg, _ = Beleg.objects.get_or_create(dboe_id=xml_id)
                beleg.orig_xml = node_as_text
                beleg.xml_file = x
                try:
                    beleg.xeno_data = xenos[i].text
                except IndexError:
                    beleg.xeno_data = "NO MATCHING ENTRY FOUND: HANSI4EVER"
                    beleg.import_issue = True
                try:
                    beleg.save(
                        add_citations=True,
                        add_lautungen=True,
                        add_sense=True,
                        add_lehnwort=True,
                        trigger_index=False,
                    )
                except Exception as e:
                    with open(failed_path, "a", encoding="utf-8") as failed_file:
                        failed_file.write(
                            f"{x}\t{xml_id}\t{str(e).replace(chr(10), ' ')}\n"
                        )
            x.belege_imported = True
            x.save()
