from xml.etree import ElementTree as ET

from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import serializers

from .models import (
    Annotation,
    Autor_Artikel,
    Category,
    Collection,
    Edit_of_article,
    Es_document,
    Lemma,
    Tag,
)


class UserSerializer(serializers.HyperlinkedModelSerializer):
    collections_created = serializers.HyperlinkedRelatedField(
        many=True, read_only=True, view_name="collection-detail"
    )
    collections_curated = serializers.HyperlinkedRelatedField(
        many=True, read_only=True, view_name="collection-detail"
    )
    annotations_created = serializers.HyperlinkedRelatedField(
        many=True, read_only=True, view_name="annotation-detail"
    )

    class Meta:
        model = User
        fields = [
            "id",
            "url",
            "username",
            "date_joined",
            "collections_created",
            "collections_curated",
            "annotations_created",
        ]


class UserListSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["id", "url", "username", "date_joined"]


class CategorySerializer(serializers.HyperlinkedModelSerializer):
    annotations = serializers.HyperlinkedRelatedField(
        many=True, read_only=True, view_name="annotation-detail"
    )

    class Meta:
        model = Category
        fields = ["id", "url", "name", "description", "note", "notation", "annotations"]


class TagSerializer(serializers.HyperlinkedModelSerializer):
    belege_count = serializers.IntegerField(read_only=True)
    belege_ids = serializers.ListField(read_only=True)

    class Meta:
        model = Tag
        fields = [
            "id",
            "name",
            "url",
            "belege_count",
            "color",
            "meta",
            "belege_ids",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get("view") and self.context["view"].action == "list":
            self.fields.pop("belege_ids", None)

    def create(self, validated_data):
        tag, _ = Tag.objects.get_or_create(
            name=validated_data.get("name", None),
            defaults={
                "color": validated_data.get("color", None),
                "meta": validated_data.get("meta", None),
            },
        )
        return tag


class Es_documentListSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Es_document
        fields = [
            "url",
            "es_id",
            "index",
            "version",
            "scans",
        ]

    def create(self, validated_data):
        es_id, _ = Es_document.objects.get_or_create(
            es_id=validated_data.get("es_id", None),
            defaults={"es_id": validated_data.get("es_id", None)},
        )
        return es_id


class Es_documentSerializer(serializers.HyperlinkedModelSerializer):
    in_collections = serializers.HyperlinkedRelatedField(
        many=True, read_only=True, view_name="collection-detail"
    )

    class Meta:
        model = Es_document
        fields = [
            "id",
            "url",
            "es_id",
            "index",
            "version",
            "tag",
            "scans",
            "xml",
            "in_collections",
            "xml_error_message",
        ]

    def validate(self, data):
        try:
            if "xml" in data and (data["xml"]):
                ET.fromstring(data["xml"])
                if self.context["request"].user.username != settings.VLE_USER:
                    data.xml_modified_by = self.context["request"].user
        except Exception as e:
            raise serializers.ValidationError(str(e))
        return data

    def create(self, validated_data):
        es_id, _ = Es_document.objects.get_or_create(
            es_id=validated_data.get("es_id", None),
            xml=validated_data.get("xml", ""),
            xml_modified_by=(
                self.context["request"].user if validated_data.get("xml") else None
            ),
            defaults={"es_id": validated_data.get("es_id", None)},
        )
        return es_id

    def update(self, instance, validated_data):
        if self.context["request"].user.username != settings.VLE_USER:
            instance.xml_modified_by = self.context["request"].user
        return super().update(instance, validated_data)


class Es_documentSerializerForScans(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Es_document
        fields = [
            "id",
            "url",
            "es_id",
            "xml",
            "scans",
        ]


class Es_documentSerializerForCache(serializers.HyperlinkedModelSerializer):
    xml_modified_by = serializers.StringRelatedField()

    class Meta:
        model = Es_document
        fields = ["id", "url", "es_id", "xml", "xml_modified_by", "xml_error_message"]


class AutorArtikelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Autor_Artikel
        fields = ["id", "url", "lemma_id", "bearbeiter_id"]


class EditOfArticleStSerializer(serializers.HyperlinkedModelSerializer):
    steps = serializers.IntegerField()
    stati = serializers.IntegerField()

    class Meta:
        model = Edit_of_article
        fields = ["step", "status", "steps", "stati"]


class EditOfArticleLemmaSerializer(serializers.HyperlinkedModelSerializer):
    lemma__lemmatisierung = serializers.CharField(read_only=True)
    document__count = serializers.IntegerField(read_only=True)
    user__username = serializers.CharField(read_only=True)

    class Meta:
        model = Edit_of_article
        fields = ["lemma__lemmatisierung", "document__count", "user__username"]


class EditOfArticleUserSerializer(serializers.HyperlinkedModelSerializer):
    user__username = serializers.CharField(read_only=True)
    lemma_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Edit_of_article
        fields = ["lemma_count", "user__username"]


class EditOfArticleSerializer(serializers.HyperlinkedModelSerializer):
    user_name = serializers.CharField(source="user.username", read_only=True)
    lemma_name = serializers.CharField(source="lemma.lemmatisierung", read_only=True)

    class Meta:
        model = Edit_of_article
        fields = [
            "id",
            "current",
            "url",
            "begin_time",
            "step",
            "status",
            "description",
            "deadline",
            "last_edited",
            "user",
            "user_name",
            "lemma",
            "lemma_name",
            "finished_date",
        ]


class LemmaSerializer(serializers.HyperlinkedModelSerializer):
    art_lemmatisierung = serializers.CharField(
        source="simplex.lemmatisierung", read_only=True
    )
    assigned_task = serializers.SerializerMethodField()

    def get_assigned_task(self, lemma) -> dict | None:
        curr_lemma = Lemma.objects.get(id=lemma.id)
        if curr_lemma.simplex is not None:
            lemma = curr_lemma.simplex
        try:
            tasks = Edit_of_article.objects.filter(
                lemma=Lemma.objects.get(id=lemma.id), current=True
            ).first()
            ser_context = {"request": self.context.get("request")}
            result = EditOfArticleSerializer(tasks, context=ser_context)
            user = result.data["user"]
            if user is None:
                return None
            else:
                return {
                    "user": result.data["user"],
                    "user_name": result.data["user_name"],
                    "task": result.data["url"],
                }
        except Edit_of_article.DoesNotExist:
            return None

    class Meta:
        model = Lemma
        fields = [
            "id",
            "url",
            "lemmatisierung",
            "norm",
            "org",
            "filename",
            "comment",
            "count",
            "simplex",
            "art_lemmatisierung",
            "assigned_task",
            "pos",
            "suggestion",
        ]


class CollectionSerializer(serializers.HyperlinkedModelSerializer):
    created_by = serializers.StringRelatedField()
    doc_count = serializers.IntegerField(read_only=True)
    tag_names = serializers.ListField(read_only=True)
    docs = serializers.ListField(read_only=True)

    class Meta:
        model = Collection
        fields = [
            "id",
            "url",
            "title",
            "lemma_id",
            "description",
            "doc_count",
            "docs",
            "tag_names",
            "comment",
            "annotations",
            "created_by",
            "curator",
            "public",
            "deleted",
            "created",
            "modified",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get("view") and self.context["view"].action == "list":
            self.fields.pop("docs", None)


class AnnotationSerializer(serializers.HyperlinkedModelSerializer):
    # created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
    created_by = serializers.StringRelatedField()

    class Meta:
        model = Annotation
        fields = [
            "id",
            "url",
            "collection",
            "title",
            "description",
            "category",
            "created_by",
            "created",
            "modified",
        ]
