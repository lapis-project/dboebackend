import django_filters

from belege.api_utils import get_verbose_name
from siglen.models import BelegSigle, Sigle, sigle_kinds


class BelegSigleFilter(django_filters.rest_framework.FilterSet):
    beleg__dboe_id = django_filters.CharFilter(label="Beleg (DBÖ-ID)")
    sigle__sigle = django_filters.CharFilter()

    class Meta:
        model = BelegSigle
        fields = ["beleg__dboe_id", "sigle__sigle"]


class SigleFilter(django_filters.rest_framework.FilterSet):
    sigle = django_filters.CharFilter(
        label=get_verbose_name(Sigle, "sigle"),
    )
    sigle_startswith = django_filters.CharFilter(
        field_name="sigle",
        label=f"{get_verbose_name(Sigle, 'sigle')} (beginnt mit)",
        lookup_expr="startswith",
    )
    name = django_filters.CharFilter(
        label=get_verbose_name(Sigle, "kind"), lookup_expr="icontains"
    )
    kind = django_filters.MultipleChoiceFilter(
        choices=sigle_kinds, label=get_verbose_name(Sigle, "kind")
    )

    class Meta:
        fields = ["sigle", "sigle_startswith", "name", "kind"]
