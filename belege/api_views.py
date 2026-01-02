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
    LautungSerializer,
    get_serializer_for_model,
)


class CustomPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 20
    page_size_query_param = "page_size"


class CustomViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend]
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.serializer_class:
            return self.serializer_class
        else:
            return get_serializer_for_model(self.queryset.model)


class FacsimileViewSet(CustomViewSet):
    queryset = Facsimile.objects.all()
    filterset_class = get_filterset_for_model(Facsimile)


class BelegViewSet(CustomViewSet):
    queryset = Beleg.objects.all()
    filterset_class = get_filterset_for_model(Beleg)


class BelegViewSetElasticSearch(viewsets.ModelViewSet):
    page_size = 10
    max_page_size = 20
    page_size_query_param = "page_size"
    pagination_class = CustomPagination
    queryset = Beleg.objects.all()
    filterset_class = get_filterset_for_model(Beleg)
    serializer_class = BelegSerializer
    # lookup_field = "dboe_id"
    # lookup_value_regex = (
    #     r"[^/]+"  # the default regex does not work with dboe_ids due to e.g. `.`
    # )


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
