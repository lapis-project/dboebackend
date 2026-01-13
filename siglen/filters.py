import django_filters

from siglen.models import BelegSigle, sigle_kinds


class BelegSigleFilter(django_filters.rest_framework.FilterSet):
    beleg__dboe_id = django_filters.CharFilter()
    sigle__sigle = django_filters.CharFilter()

    class Meta:
        model = BelegSigle
        fields = ["beleg__dboe_id", "sigle__sigle"]


class SigleFilter(django_filters.rest_framework.FilterSet):
    name = django_filters.CharFilter(
        label="Name", help_text="Name", lookup_expr="icontains"
    )
    kind = django_filters.MultipleChoiceFilter(choices=sigle_kinds)

    class Meta:
        fields = ["sigle", "name", "kind"]
