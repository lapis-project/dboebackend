from django.conf import settings
from django.db import reset_queries

from belege.api_views import CustomViewSet
from belege.query_utils import log_query_count
from siglen.filters import BelegSigleFilter, SigleFilter
from siglen.models import BelegSigle, Sigle
from siglen.serializers import BelegSigleSerializer, SigleSerializer


class SigleViewSet(CustomViewSet):
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


class BeleSigleViewSet(CustomViewSet):
    queryset = BelegSigle.objects.all()
    serializer_class = BelegSigleSerializer
    filterset_class = BelegSigleFilter

    def list(self, request, *args, **kwargs):
        reset_queries()
        response = super().list(request, *args, **kwargs)
        if settings.DEBUG:
            log_query_count(full_log=False)
        return response
