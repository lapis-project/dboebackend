from rest_framework import serializers

from belege.models import Beleg, Citation, Lautung


def get_serializer_for_model(model_class, field_to_serialize="__all__"):
    class DynamicSerlizer(serializers.HyperlinkedModelSerializer):
        class Meta:
            model = model_class
            fields = field_to_serialize

    return DynamicSerlizer


class BelegSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="belege-elastic-search-detail")
    hl = serializers.CharField(source="hauptlemma", required=False)
    nl = serializers.CharField(source="nebenlemma", required=False)
    id = serializers.CharField(source="dboe_id", required=False)
    qu = serializers.CharField(source="quelle", required=False)

    class Meta:
        model = Beleg
        fields = [
            "url",
            "id",
            "hl",
            "nl",
            "qu",
            "bibl",
            "pos",
            "archivzeile",
        ]

    def get_locationcenter(self, instance):
        return instance.dboe_id[-1] if instance.dboe_id else None

    def get_locationcenter_quq(self, instance):
        return "48.033199664024224,13.996338548539455"

    def to_representation(self, instance):
        # Obtain the base representation from the parent class (core fields + url)
        base = super().to_representation(instance)
        # Delegate to model helper for enrichment
        return instance.build_representation(base=base)


class CitationSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="citation-detail", lookup_field="dboe_id"
    )
    id = serializers.CharField(source="dboe_id", read_only=False)
    beleg_id = serializers.CharField(source="beleg.dboe_id", read_only=True)
    orig_xml = serializers.CharField(read_only=True)

    class Meta:
        model = Citation
        fields = "__all__"


class LautungSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="lautung-detail", lookup_field="dboe_id"
    )
    id = serializers.CharField(source="dboe_id", read_only=False)
    beleg_id = serializers.CharField(source="beleg.dboe_id", read_only=True)
    orig_xml = serializers.CharField(read_only=True)

    class Meta:
        model = Lautung
        fields = "__all__"
