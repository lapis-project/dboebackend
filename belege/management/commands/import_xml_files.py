import glob
import os

from acdh_tei_pyutils.tei import TeiReader
from django.core.management.base import BaseCommand
from tqdm import tqdm

from belege.models import DboeXmlFile


class Command(BaseCommand):
    help = "creates DBO-XML file objects"

    def handle(self, *args, **options):
        files = sorted(glob.glob("/home/csae8092/repos/dboe/dboe2arche/data/*.xml"))
        for x in tqdm(files, total=len(files)):
            dboe_id = os.path.split(x)[-1]
            item = DboeXmlFile.objects.get_or_create(dboe_id=dboe_id)[0]
            doc = TeiReader(x)
            item.nr_belege = len(doc.any_xpath(".//tei:entry[@xml:id]"))
            item.save()
