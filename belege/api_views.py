import lxml.etree as ET
from django.conf import settings
from django.db import reset_queries
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    extend_schema,
    inline_serializer,
)
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from belege.api_utils import get_filterset_for_model
from belege.models import (
    PERIOD_CHOICES,
    POS_CHOICES,
    Annotation,
    Beleg,
    Citation,
    Lautung,
    LehnWort,
    Sense,
)
from belege.query_utils import log_query_count
from belege.serializers import (
    AnnotationSerializer,
    BelegSerializer,
    CitationSerializer,
    LautungSerializer,
    LehnWortSerializer,
    SenseSerializer,
)


@extend_schema(
    responses={
        200: inline_serializer(
            name="PosTag",
            fields={
                "label": serializers.CharField(),
                "value": serializers.CharField(),
            },
            many=True,
        )
    }
)
@api_view(["get"])
def get_pos_tags(request):
    data = [{"label": x[1], "value": x[0]} for x in POS_CHOICES]
    return JsonResponse(data, safe=False)


@extend_schema(
    responses={
        200: inline_serializer(
            name="Period",
            fields={
                "label": serializers.CharField(),
                "value": serializers.CharField(),
            },
            many=True,
        )
    }
)
@api_view(["get"])
def get_periods(request):
    data = [{"label": x[1], "value": x[0]} for x in PERIOD_CHOICES]
    return JsonResponse(data, safe=False)


@extend_schema(responses={200: OpenApiTypes.STR})
@api_view(["get"])
def show_original_xml(request, dboe_id):
    """Return the original TEI/XML entry"""
    beleg = get_object_or_404(Beleg, pk=dboe_id)
    payload = ET.tostring(beleg.orig_xml).decode("utf-8")
    return HttpResponse(payload, content_type="application/xml")


@extend_schema(responses={200: OpenApiTypes.STR})
@api_view(["get"])
def show_tustep(request, dboe_id):
    """Return the original Tustep data"""
    beleg = get_object_or_404(Beleg, pk=dboe_id)
    payload = beleg.xeno_data
    return HttpResponse(payload, content_type="text/plain")


class CustomPagination(PageNumberPagination):
    page_size = 50
    max_page_size = 50
    page_size_query_param = "page_size"


class BelegePagination(PageNumberPagination):
    page_size = 50
    max_page_size = 1000
    page_size_query_param = "page_size"


class BelegViewSetElasticSearch(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    pagination_class = BelegePagination
    queryset = Beleg.objects.with_related()
    filterset_class = get_filterset_for_model(
        Beleg, fields=["dboe_id", "collection", "has_internal_comment", "has_scan"]
    )
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
    @action(detail=False, methods=["post"], permission_classes=[])
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
    queryset = Citation.objects.prefetch_related("annotation").all()
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


class AnnotationViewSet(viewsets.ModelViewSet):
    pagination_class = CustomPagination
    page_size_query_param = "page_size"
    queryset = Annotation.objects.select_related("kontext").all()
    filterset_class = get_filterset_for_model(
        Annotation, fields=["id", "kontext", "tool", "source_field"]
    )
    serializer_class = AnnotationSerializer

    def list(self, request, *args, **kwargs):
        reset_queries()
        response = super().list(request, *args, **kwargs)
        if settings.DEBUG:
            log_query_count(full_log=False)
        return response
