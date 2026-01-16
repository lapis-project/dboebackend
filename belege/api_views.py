from django.conf import settings
from django.db import reset_queries
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from belege.api_utils import get_filterset_for_model
from belege.models import (
    AnmerkungLautung,
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
    AnmerkungLautungSerializer,
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

    @extend_schema(
        summary="Filter Beleg objects by a list of IDs",
        description="Returns a paginated list of Beleg objects filtered by the provided dboe_id values. "
        "Accepts a list of IDs in the request body and returns the standard Beleg serialization.",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of dboe_id values to filter by",
                    }
                },
                "required": ["ids"],
            }
        },
        responses={200: BelegSerializer(many=True)},
        examples=[
            OpenApiExample(
                "Example request",
                value={"ids": ["b120_qdbn-d16e2", "b120_qdbn-d16e30"]},
                request_only=True,
            )
        ],
    )
    @action(detail=False, methods=["post"])
    def filter_by_ids(self, request):
        reset_queries()
        ids = request.data.get("ids", [])
        queryset = self.filter_queryset(self.get_queryset().filter(dboe_id__in=ids))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(queryset, many=True)
            response = Response(serializer.data)

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


class AnmerkungLautungViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    pagination_class = CustomPagination
    page_size_query_param = "page_size"
    queryset = AnmerkungLautung.objects.all()
    filterset_class = get_filterset_for_model(
        AnmerkungLautung, fields=["dboe_id", "beleg"]
    )
    serializer_class = AnmerkungLautungSerializer
    lookup_field = "dboe_id"
    lookup_value_regex = r"[^/]+"

    def list(self, request, *args, **kwargs):
        reset_queries()
        response = super().list(request, *args, **kwargs)
        if settings.DEBUG:
            log_query_count(full_log=False)
        return response
