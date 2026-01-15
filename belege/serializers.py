from rest_framework import serializers

from annotations.models import Tag
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
from belege.serializer_utils import PopulateLabelMixin


class FacsimilieSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Facsimile
        fields = [
            "url",
            "file_name",
        ]


class BelegSerializer(PopulateLabelMixin, serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="belege-elastic-search-detail", read_only=True
    )
    hl = serializers.CharField(source="hauptlemma", required=False)
    nl = serializers.CharField(source="nebenlemma", required=False, allow_null=True)
    id = serializers.CharField(source="dboe_id", read_only=True)
    qu = serializers.CharField(source="quelle", required=False, allow_null=True)
    modify_tag = serializers.PrimaryKeyRelatedField(
        source="tag",
        many=True,
        queryset=Tag.objects.all(),
        read_only=False,
        allow_null=True,
    )

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
            "modify_tag",
        ]

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")

        # Only include 'tag' field for PUT and PATCH requests
        if request and request.method not in ["PUT", "PATCH"]:
            fields.pop("modify_tag", None)

        return fields

    def get_locationcenter(self, instance):
        return instance.dboe_id[-1] if instance.dboe_id else None

    def get_locationcenter_quq(self, instance):
        return "48.033199664024224,13.996338548539455"

    def to_representation(self, instance):
        # Obtain the base representation from the parent class (core fields + url)
        base = super().to_representation(instance)
        # Delegate to model helper for enrichment
        return instance.build_representation(base=base)


class CitationSerializer(PopulateLabelMixin, serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="citation-detail", lookup_field="dboe_id"
    )
    id = serializers.CharField(source="dboe_id", read_only=True)
    beleg = serializers.PrimaryKeyRelatedField(read_only=True)
    orig_xml = serializers.CharField(read_only=True)

    class Meta:
        model = Citation
        fields = "__all__"


class LautungSerializer(PopulateLabelMixin, serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="lautung-detail", lookup_field="dboe_id"
    )
    beleg = serializers.PrimaryKeyRelatedField(read_only=True)
    id = serializers.CharField(source="dboe_id", read_only=True)
    orig_xml = serializers.CharField(read_only=True)

    class Meta:
        model = Lautung
        fields = "__all__"


class LehnWortSerializer(PopulateLabelMixin, serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="lehnwort-detail", lookup_field="dboe_id"
    )
    id = serializers.CharField(source="dboe_id", read_only=True)
    beleg = serializers.PrimaryKeyRelatedField(read_only=True)
    orig_xml = serializers.CharField(read_only=True)

    class Meta:
        model = LehnWort
        fields = "__all__"


class BelegFacsSerializer(PopulateLabelMixin, serializers.HyperlinkedModelSerializer):
    id = serializers.CharField(read_only=True)
    beleg = serializers.PrimaryKeyRelatedField(queryset=Beleg.objects.all())
    facsimile = serializers.PrimaryKeyRelatedField(queryset=Facsimile.objects.all())

    class Meta:
        model = BelegFacs
        fields = "__all__"


class SenseSerializer(PopulateLabelMixin, serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="sense-detail", lookup_field="dboe_id"
    )
    id = serializers.CharField(source="dboe_id", read_only=True)
    beleg = serializers.PrimaryKeyRelatedField(read_only=True)
    orig_xml = serializers.CharField(read_only=True)

    class Meta:
        model = Sense
        fields = "__all__"


class AnmerkungLautungSerializer(
    PopulateLabelMixin, serializers.HyperlinkedModelSerializer
):
    url = serializers.HyperlinkedIdentityField(
        view_name="anmerkunglautung-detail", lookup_field="dboe_id"
    )
    id = serializers.CharField(source="dboe_id", read_only=True)
    beleg = serializers.PrimaryKeyRelatedField(read_only=True)
    orig_xml = serializers.CharField(read_only=True)

    class Meta:
        model = AnmerkungLautung
        fields = "__all__"
