from rest_framework import serializers

from belege.models import Beleg
from belege.serializer_utils import PopulateLabelMixin
from siglen.models import BelegSigle, Sigle


class SigleSerializer(PopulateLabelMixin, serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="sigle-detail", read_only=True, required=False, lookup_field="sigle"
    )
    sigle = serializers.CharField(read_only=False, required=True)
    bl = serializers.PrimaryKeyRelatedField(
        queryset=Sigle.objects.all(), required=False, allow_null=True
    )
    gr = serializers.PrimaryKeyRelatedField(
        queryset=Sigle.objects.all(), required=False, allow_null=True
    )
    kr = serializers.PrimaryKeyRelatedField(
        queryset=Sigle.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Sigle
        fields = [
            "url",
            "sigle",
            "name",
            "kind",
            "coordinates",
            "geonames",
            "bl",
            "gr",
            "kr",
        ]


class BelegSigleSerializer(serializers.HyperlinkedModelSerializer):
    beleg = serializers.PrimaryKeyRelatedField(queryset=Beleg.objects.all())
    sigle = serializers.PrimaryKeyRelatedField(queryset=Sigle.objects.all())

    class Meta:
        model = BelegSigle
        fields = ["id", "beleg", "sigle", "corresp", "resp"]
