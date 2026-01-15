from django.conf import settings
from django.db import reset_queries
from rest_framework import mixins, viewsets
from rest_framework.pagination import PageNumberPagination

from belege.api_utils import get_filterset_for_model
from belege.models import (
    Beleg,
    BelegFacs,
    Citation,
    Facsimile,
    Lautung,
    LehnWort,
    Sense,
)
from belege.query_utils import log_query_count
from belege.serializers import (
    BelegFacsSerializer,
    BelegSerializer,
    CitationSerializer,
    FacsimilieSerializer,
    LautungSerializer,
    LehnWortSerializer,
    SenseSerializer,
)


class CustomPagination(PageNumberPagination):
    page_size = 50
    max_page_size = 50
    page_size_query_param = "page_size"


class BelegFacsViewset(viewsets.ModelViewSet):
    pagination_class = CustomPagination
    queryset = BelegFacs.objects.all()
    serializer_class = BelegFacsSerializer
    filterset_class = get_filterset_for_model(BelegFacs)

    def list(self, request, *args, **kwargs):
        reset_queries()
        response = super().list(request, *args, **kwargs)
        if settings.DEBUG:
            log_query_count(full_log=False)
        return response


class FacsimileViewSet(viewsets.ModelViewSet):
    pagination_class = CustomPagination
    queryset = Facsimile.objects.all()
    serializer_class = FacsimilieSerializer
    filterset_class = get_filterset_for_model(Facsimile)

    def list(self, request, *args, **kwargs):
        reset_queries()
        response = super().list(request, *args, **kwargs)
        if settings.DEBUG:
            log_query_count(full_log=False)
        return response


class BelegViewSetElasticSearch(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    pagination_class = CustomPagination
    queryset = Beleg.objects.with_related()
    filterset_class = get_filterset_for_model(Beleg, fields=["dboe_id", "collection"])
    serializer_class = BelegSerializer

    def list(self, request, *args, **kwargs):
        reset_queries()
        response = super().list(request, *args, **kwargs)
        if settings.DEBUG:
            log_query_count(full_log=False)
        return response


class CitationViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    pagination_class = CustomPagination
    page_size_query_param = "page_size"
    queryset = Citation.objects.all()
    filterset_class = get_filterset_for_model(Citation, fields=["dboe_id", "beleg"])
    serializer_class = CitationSerializer
    lookup_field = "dboe_id"
    lookup_value_regex = r"[^/]+"

    def list(self, request, *args, **kwargs):
        reset_queries()
        response = super().list(request, *args, **kwargs)
        if settings.DEBUG:
            log_query_count(full_log=False)
        return response


class LautungViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    pagination_class = CustomPagination
    page_size_query_param = "page_size"
    queryset = Lautung.objects.all()
    filterset_class = get_filterset_for_model(Lautung, fields=["dboe_id", "beleg"])
    serializer_class = LautungSerializer
    lookup_field = "dboe_id"
    lookup_value_regex = r"[^/]+"

    def list(self, request, *args, **kwargs):
        reset_queries()
        response = super().list(request, *args, **kwargs)
        if settings.DEBUG:
            log_query_count(full_log=False)
        return response


class LehnwortViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    pagination_class = CustomPagination
    page_size_query_param = "page_size"
    queryset = LehnWort.objects.all()
    filterset_class = get_filterset_for_model(LehnWort, fields=["dboe_id", "beleg"])
    serializer_class = LehnWortSerializer
    lookup_field = "dboe_id"
    lookup_value_regex = r"[^/]+"

    def list(self, request, *args, **kwargs):
        reset_queries()
        response = super().list(request, *args, **kwargs)
        if settings.DEBUG:
            log_query_count(full_log=False)
        return response


class SenseViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    pagination_class = CustomPagination
    page_size_query_param = "page_size"
    queryset = Sense.objects.all()
    filterset_class = get_filterset_for_model(Sense, fields=["dboe_id", "beleg"])
    serializer_class = SenseSerializer
    lookup_field = "dboe_id"
    lookup_value_regex = r"[^/]+"

    def list(self, request, *args, **kwargs):
        reset_queries()
        response = super().list(request, *args, **kwargs)
        if settings.DEBUG:
            log_query_count(full_log=False)
        return response
