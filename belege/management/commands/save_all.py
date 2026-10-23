from django.core.management.base import BaseCommand
from tqdm import tqdm

from belege.models import Beleg, DboeXmlFile


class Command(BaseCommand):
    help = "saves all Beleg objects, file by file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--starts_with",
            type=str,
            default=None,
            help="only save belege of files whose dboe_id starts with this value",
        )

    def handle(self, *args, **options):
        files = DboeXmlFile.objects.all().order_by("dboe_id")
        starts_with = options.get("starts_with")
        if starts_with:
            files = files.filter(dboe_id__startswith=starts_with)
        total_files = files.count()
        print(f"saving belege from {total_files} files")
        for f, xml_file in enumerate(files, start=1):
            belege = Beleg.objects.filter(xml_file=xml_file)
            print(f"{f}/{total_files} files: {xml_file.dboe_id}")
            for x in tqdm(belege.iterator(), total=belege.count()):
                try:
                    x.save(trigger_index=False)
                except Exception as e:
                    print(x.dboe_id, e)
                    continue
        print("done")
