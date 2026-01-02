import json
import os

from django.core.management.base import BaseCommand
from tqdm import tqdm

from siglen.models import Sigle


class Command(BaseCommand):
    help = "imports places"

    def handle(self, *args, **options):
        with open(os.path.join("data", "places.json"), "r", encoding="utf-8") as fp:
            data = json.load(fp)
        for value in tqdm(data.values()):
            try:
                Sigle.objects.get_or_create(
                    sigle=value["Bundesland"]["idno"],
                    name=value["Bundesland"]["label"],
                    kind="bl",
                )
            except Exception as e:
                print(f"Error creating Sigle {value} due to: {e}")
            try:
                if value["Großregion"]["idno"]:
                    Sigle.objects.get_or_create(
                        sigle=value["Großregion"]["idno"],
                        name=value["Großregion"]["label"],
                        kind="gr",
                    )
            except Exception as e:
                print(f"Error creating Sigle {value} due to: {e}")
            try:
                if value["Kleinregion"]["idno"]:
                    Sigle.objects.get_or_create(
                        sigle=value["Kleinregion"]["idno"],
                        name=value["Kleinregion"]["label"],
                        kind="kr",
                    )
            except Exception as e:
                print(f"Error creating Sigle {value} due to: {e}")
            try:
                if value["Ort"]["idno"]:
                    Sigle.objects.get_or_create(
                        sigle=value["Ort"]["idno"],
                        name=value["Ort"]["label"],
                        kind="ort",
                    )
            except Exception as e:
                print(f"Error creating Sigle {value} due to: {e}")
        for value in tqdm(data.values()):
            if value["Ort"]["idno"]:
                try:
                    item = Sigle.objects.get(sigle=value["Ort"]["idno"])
                except Sigle.DoesNotExist:
                    print(f"Ort Sigle does not exist: {value['Ort']['idno']}")
                    continue
                try:
                    item.kr = Sigle.objects.get(sigle=value["Kleinregion"]["idno"])
                except Sigle.DoesNotExist:
                    item.kr = None
                try:
                    item.gr = Sigle.objects.get(sigle=value["Großregion"]["idno"])
                except Sigle.DoesNotExist:
                    item.gr = None
                try:
                    item.bl = Sigle.objects.get(sigle=value["Bundesland"]["idno"])
                except Sigle.DoesNotExist:
                    item.bl = None
                item.save()
            if value["Kleinregion"]["idno"]:
                item = Sigle.objects.get(sigle=value["Kleinregion"]["idno"])
                try:
                    item.gr = Sigle.objects.get(sigle=value["Großregion"]["idno"])
                except Sigle.DoesNotExist:
                    item.gr = None
                try:
                    item.bl = Sigle.objects.get(sigle=value["Bundesland"]["idno"])
                except Sigle.DoesNotExist:
                    item.bl = None
                item.save()
            if value["Großregion"]["idno"]:
                item = Sigle.objects.get(sigle=value["Großregion"]["idno"])
                try:
                    item.bl = Sigle.objects.get(sigle=value["Bundesland"]["idno"])
                except Sigle.DoesNotExist:
                    item.bl = None
                item.save()
        print("done")
