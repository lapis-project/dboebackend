import json
import os
from time import sleep

from django.conf import settings
from django.core.management.base import BaseCommand
from opensearchpy.helpers import bulk
from tqdm import tqdm

from belege.models import Beleg
from belege.opensearch_client import OS_INDEX_NAME, client

beleg_json_dir = os.path.join(settings.MEDIA_ROOT, "belege")
os.makedirs(beleg_json_dir, exist_ok=True)


class Command(BaseCommand):
    help = "indexing Belege"

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1500,
            help="Number of records per JSON batch file (default: 1500)",
        )
        parser.add_argument(
            "--dump",
            action="store_true",
            default=False,
            help="Write batch files to disk (default: False)",
        )

    def handle(self, *args, **options):
        cur_nr = 0
        batch_size = options.get("batch_size") or 1500
        dump_to_file = options.get("dump", False)
        if batch_size <= 0:
            raise ValueError("batch-size must be a positive integer")

        total = Beleg.objects.count()
        queryset = Beleg.objects.with_related().order_by("dboe_id")

        batch = []
        beleg_ids_in_batch = []

        for x in tqdm(queryset.iterator(chunk_size=batch_size), total=total):
            cur_nr += 1
            beleg_ids_in_batch.append(x.dboe_id)
            batch.append(x)

            if len(batch) >= batch_size:
                actions = []
                for x in batch:
                    try:
                        serialized = x.sanitize_representation()
                        actions.append(
                            {
                                "_op_type": "index",
                                "_index": OS_INDEX_NAME,
                                "_id": serialized["id"],
                                "_source": serialized,
                            }
                        )
                    except Exception as e:
                        print(f"failed to serialize {x} due to {e}")
                        continue

                _, failed = bulk(client, actions)
                sleep(2)
                if failed:
                    print(f"{failed=}")

                if dump_to_file:
                    serialized_batch = []
                    for x in batch:
                        try:
                            serialized_batch.append(x.sanitize_representation())
                        except Exception as e:
                            print(f"failed to serialize {x} due to {e}")
                            continue

                    out_file = f"belege_{cur_nr:05}.json"
                    save_path = os.path.join(beleg_json_dir, out_file)
                    with open(save_path, "w", encoding="utf-8") as fp:
                        json.dump(serialized_batch, fp, ensure_ascii=False)
                    print(f"wrote {len(serialized_batch)} records to {save_path}")

                batch = []
                beleg_ids_in_batch = []

        # Flush remaining records (if any)
        if batch:
            actions = []
            for x in batch:
                try:
                    serialized = x.sanitize_representation()
                    actions.append(
                        {
                            "_op_type": "index",
                            "_index": OS_INDEX_NAME,
                            "_id": serialized["id"],
                            "_source": serialized,
                        }
                    )
                except Exception as e:
                    print(f"failed to serialize {x} due to {e}")
                    continue

            _, failed = bulk(client, actions)
            if failed:
                print(f"{failed=}")

            if dump_to_file:
                serialized_batch = []
                for x in batch:
                    try:
                        serialized_batch.append(x.sanitize_representation())
                    except Exception as e:
                        print(f"failed to serialize {x} due to {e}")
                        continue

                out_file = f"belege_{cur_nr:05}.json"
                save_path = os.path.join(beleg_json_dir, out_file)
                with open(save_path, "w", encoding="utf-8") as fp:
                    json.dump(serialized_batch, fp, ensure_ascii=False)
                print(f"wrote final {len(serialized_batch)} records to {save_path}")

        print("done (all batches written)")
