from django.conf import settings
from django.db import reset_queries
from rest_framework import viewsets

from belege.api_views import CustomPagination
from belege.query_utils import log_query_count
from siglen.filters import BelegSigleFilter, SigleFilter
from siglen.models import BelegSigle, Sigle
from siglen.serializers import BelegSigleSerializer, SigleSerializer


class SigleViewSet(viewsets.ModelViewSet):
    pagination_class = CustomPagination
    queryset = Sigle.objects.all()
    serializer_class = SigleSerializer
    filterset_class = SigleFilter
    lookup_field = "sigle"
    lookup_value_regex = r"[^/]+"

    def list(self, request, *args, **kwargs):
        reset_queries()
        response = super().list(request, *args, **kwargs)
        if settings.DEBUG:
            log_query_count(full_log=False)
        return response


class BeleSigleViewSet(viewsets.ModelViewSet):
    pagination_class = CustomPagination
    queryset = BelegSigle.objects.all()
    serializer_class = BelegSigleSerializer
    filterset_class = BelegSigleFilter

    def list(self, request, *args, **kwargs):
        reset_queries()
        response = super().list(request, *args, **kwargs)
        if settings.DEBUG:
            log_query_count(full_log=False)
        return response
