from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from belege.api_utils import get_filterset_for_model
from belege.models import (
    Beleg,
    Citation,
    Facsimile,
    Lautung,
)
from belege.serializers import (
    BelegSerializer,
    CitationSerializer,
    FacsimilieSerializer,
    LautungSerializer,
)


class CustomPagination(PageNumberPagination):
    page_size = 50
    max_page_size = 50
    page_size_query_param = "page_size"


class CustomViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend]
    pagination_class = CustomPagination


class FacsimileViewSet(CustomViewSet):
    queryset = Facsimile.objects.all()
    serializer_class = FacsimilieSerializer
    filterset_class = get_filterset_for_model(Facsimile)


class BelegViewSet(CustomViewSet):
    queryset = Beleg.objects.with_related()
    filterset_class = get_filterset_for_model(Beleg)


class BelegViewSetElasticSearch(viewsets.ModelViewSet):
    pagination_class = CustomPagination
    queryset = Beleg.objects.with_related()
    filterset_class = get_filterset_for_model(Beleg)
    serializer_class = BelegSerializer

    # def list(self, request, *args, **kwargs):
    #     reset_queries()
    #     response = super().list(request, *args, **kwargs)

    #     # Log query information
    #     queries = connection.queries
    #     print(f"\n{'=' * 80}")
    #     print(f"Total queries executed: {len(queries)}")
    #     print(f"{'=' * 80}")

    #     # Group queries by type
    #     query_types = {}
    #     for i, query in enumerate(queries, 1):
    #         sql = query["sql"]
    #         time = query["time"]

    #         # Extract table name
    #         if "FROM" in sql:
    #             table = sql.split("FROM")[1].split()[0].strip('"')
    #         elif "UPDATE" in sql:
    #             table = sql.split("UPDATE")[1].split()[0].strip('"')
    #         else:
    #             table = "unknown"

    #         query_types[table] = query_types.get(table, 0) + 1

    #         # Print first 5 and last 5 queries with details
    #         if i <= 5 or i > len(queries) - 5:
    #             print(f"\nQuery {i} ({time}s) - Table: {table}")
    #             print(f"{sql[:200]}..." if len(sql) > 200 else sql)

    #     print(f"\n{'=' * 80}")
    #     print("Queries by table:")
    #     for table, count in sorted(
    #         query_types.items(), key=lambda x: x[1], reverse=True
    #     ):
    #         print(f"  {table}: {count}")
    #     print(f"{'=' * 80}\n")

    #     return response


class CitationViewSet(viewsets.ModelViewSet):
    page_size = 10
    max_page_size = 20
    page_size_query_param = "page_size"
    pagination_class = CustomPagination
    queryset = Citation.objects.all()
    filterset_class = get_filterset_for_model(Citation)
    serializer_class = CitationSerializer
    lookup_field = "dboe_id"
    lookup_value_regex = (
        r"[^/]+"  # the default regex does not work with dboe_ids due to e.g. `.`
    )


class LautungViewSet(viewsets.ModelViewSet):
    page_size = 10
    max_page_size = 20
    page_size_query_param = "page_size"
    pagination_class = CustomPagination
    queryset = Lautung.objects.all()
    filterset_class = get_filterset_for_model(Lautung)
    serializer_class = LautungSerializer
    lookup_field = "dboe_id"
    lookup_value_regex = r"[^/]+"
