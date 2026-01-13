from rest_framework import serializers

from belege.models import Beleg
from siglen.models import BelegSigle, Sigle


class SigleSerializer(serializers.HyperlinkedModelSerializer):
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            source = getattr(field, "source", field_name)
            if source and source != "*":
                try:
                    model_field = self.Meta.model._meta.get_field(source)
                    if (
                        hasattr(model_field, "verbose_name")
                        and model_field.verbose_name
                    ):
                        field.label = model_field.verbose_name
                except Exception:
                    pass


class BelegSigleSerializer(serializers.HyperlinkedModelSerializer):
    beleg = serializers.PrimaryKeyRelatedField(queryset=Beleg.objects.all())
    sigle = serializers.PrimaryKeyRelatedField(queryset=Sigle.objects.all())

    class Meta:
        model = BelegSigle
        fields = ["id", "beleg", "sigle", "corresp", "resp"]
