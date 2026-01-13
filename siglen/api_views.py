from belege.api_views import CustomViewSet
from siglen.filters import BelegSigleFilter, SigleFilter
from siglen.models import BelegSigle, Sigle
from siglen.serializers import BelegSigleSerializer, SigleSerializer


class SigleViewSet(CustomViewSet):
    queryset = Sigle.objects.all()
    serializer_class = SigleSerializer
    filterset_class = SigleFilter
    lookup_field = "sigle"
    lookup_value_regex = (
        r"[^/]+"  # the default regex does not work with dboe_ids due to e.g. `.`
    )


class BeleSigleViewSet(CustomViewSet):
    queryset = BelegSigle.objects.all()
    serializer_class = BelegSigleSerializer
    filterset_class = BelegSigleFilter
