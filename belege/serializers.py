from drf_spectacular.utils import extend_schema_field, extend_schema_serializer
from rest_framework import serializers

from annotations.models import Tag
from belege.models import (
    DEF_SCHEMA,
    ETYMOLOGY_SCHEMA,
    NOTES_SCHEMA,
    RE_SCHEMA,
    REFS_SCHEMA,
    VERWEIS_SCHEMA,
    XR_SCHEMA,
    Annotation,
    Beleg,
    Citation,
    Lautung,
    LehnWort,
    Sense,
)
from belege.serializer_utils import PopulateLabelMixin
from bibls.models import BibliographicType


@extend_schema_field(ETYMOLOGY_SCHEMA)
class EtymologyField(serializers.JSONField):
    """JSONField whose OpenAPI schema mirrors the model's ETYMOLOGY_SCHEMA."""


@extend_schema_field(DEF_SCHEMA)
class DefinitionNodeField(serializers.JSONField):
    """JSONField whose OpenAPI schema mirrors the model's DEF_SCHEMA."""


@extend_schema_field(NOTES_SCHEMA)
class NoteField(serializers.JSONField):
    """JSONField whose OpenAPI schema mirrors the model's NOTES_SCHEMA."""


@extend_schema_field(XR_SCHEMA)
class XrNodeField(serializers.JSONField):
    """JSONField whose OpenAPI schema mirrors the model's XR_SCHEMA."""


@extend_schema_field(RE_SCHEMA)
class ReNodeField(serializers.JSONField):
    """JSONField whose OpenAPI schema mirrors the model's RE_SCHEMA."""


@extend_schema_field(REFS_SCHEMA)
class RefNodeField(serializers.JSONField):
    """JSONField whose OpenAPI schema mirrors the model's REF_SCHEMA."""


@extend_schema_field(VERWEIS_SCHEMA)
class VerweisLemmaField(serializers.JSONField):
    """JSONField whose OpenAPI schema mirrors the model's REF_SCHEMA."""


class BelegSerializer(PopulateLabelMixin, serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="belege-elastic-search-detail", read_only=True
    )
    hl = serializers.CharField(source="hauptlemma", required=False)
    hl_norm = serializers.CharField(
        source="hauptlemma_norm", required=False, allow_blank=True, allow_null=True
    )
    nl = serializers.CharField(
        source="nebenlemma", required=False, allow_blank=True, allow_null=True
    )
    id = serializers.CharField(source="dboe_id", read_only=True)
    qu = serializers.CharField(
        source="quelle", required=False, allow_blank=True, allow_null=True
    )
    qdb = serializers.CharField(
        source="quelle_bearbeitet", required=False, allow_blank=True, allow_null=True
    )
    year = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    internal_comment = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    modify_tag = serializers.PrimaryKeyRelatedField(
        source="tag",
        many=True,
        queryset=Tag.objects.all(),
        read_only=False,
        allow_null=True,
    )
    quelle_type_id = serializers.PrimaryKeyRelatedField(
        source="quelle_type",
        many=False,
        queryset=BibliographicType.objects.all(),
        read_only=False,
        allow_null=True,
    )
    etymology = EtymologyField(required=False, allow_null=True)
    note = NoteField(required=False, allow_null=True)
    xr = XrNodeField(required=False, allow_null=True)
    ref = RefNodeField(required=False, allow_null=True)
    verweislemma = RefNodeField(required=False, allow_null=True)

    class Meta:
        model = Beleg
        fields = [
            "url",
            "id",
            "hl",
            "hl_norm",
            "verweislemma",
            "nl",
            "qu",
            "quelle_number",
            "qdb",
            "bibl",
            "scan",
            "year",
            "pos",
            "archivzeile",
            "modify_tag",
            "internal_comment",
            "quelle_type_id",
            "etymology",
            "note",
            "xr",
            "ref",
            "place_qu",
            "place_qdb",
            "figure",
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


class AnnotationNestedSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="annotation-pos-detail")

    class Meta:
        model = Annotation
        fields = [
            "url",
            "id",
            "payload",
            "tool",
            "source_field",
            "created_at",
            "updated_at",
        ]


class CitationSerializer(PopulateLabelMixin, serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="citation-detail", lookup_field="dboe_id"
    )
    id = serializers.CharField(source="dboe_id", read_only=True)
    beleg = serializers.PrimaryKeyRelatedField(read_only=True)
    orig_xml = serializers.CharField(read_only=True)
    annotations = AnnotationNestedSerializer(
        source="annotation", many=True, read_only=True
    )
    definition_node = DefinitionNodeField(required=False, allow_null=True)
    note = NoteField(required=False, allow_null=True)
    xr_node = XrNodeField(required=False, allow_null=True)
    re_node = ReNodeField(required=False, allow_null=True)

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


class SenseSerializer(PopulateLabelMixin, serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="sense-detail", lookup_field="dboe_id"
    )
    id = serializers.CharField(source="dboe_id", read_only=True)
    beleg = serializers.PrimaryKeyRelatedField(read_only=True)
    orig_xml = serializers.CharField(read_only=True)
    note = NoteField(required=False, allow_null=True)

    class Meta:
        model = Sense
        fields = "__all__"


@extend_schema_serializer(component_name="BelegeAnnotation")
class AnnotationSerializer(PopulateLabelMixin, serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="annotation-pos-detail")
    kontext = serializers.PrimaryKeyRelatedField(
        queryset=Citation.objects.all(),
        style={"base_template": "input.html"},
    )

    class Meta:
        model = Annotation
        fields = "__all__"
        extra_kwargs = {
            "kontext": {
                "view_name": "citation-detail",
                "lookup_field": "dboe_id",
            }
        }
