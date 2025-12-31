from enum import Enum

from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Category(models.Model):
    """Controlled vocabulary Class"""

    name = models.CharField(max_length=255, verbose_name="Name")
    description = models.TextField(
        blank=True, help_text="Describe the purpose of this category"
    )
    note = models.TextField(blank=True, help_text="Note/Comment")
    notation = models.CharField(max_length=200, blank=True, verbose_name="Notation")

    def __str__(self):
        return "{}".format(self.name)


class Tag(models.Model):
    """Class to store tags for incoming elasticsearch documents"""

    name = models.CharField(max_length=255)
    color = models.CharField(max_length=255, blank=True)
    meta = models.JSONField(null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ["name"]


class Es_document(models.Model):
    es_id = models.CharField(max_length=255, verbose_name="ID in elasticsearch index")
    index = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Index"
    )
    version = models.IntegerField(blank=True, null=True, verbose_name="Version")
    tag = models.ManyToManyField(Tag, related_name="es_documents", blank=True)
    scans = ArrayField(
        models.CharField(max_length=200, blank=True),
        null=True,
    )

    xml = models.TextField(blank=True, help_text="XML Entry Data")
    xml_modified_by = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="xml_modified",
        help_text="The user updated the xml field",
    )
    xml_error_message = models.TextField(
        blank=True, help_text="Field for for wboe api to store validation error message"
    )

    def __str__(self):
        return "ID {}: {}".format(self.id, self.es_id)


class Lemma(models.Model):
    """Class to store tags for incoming elasticsearch documents"""

    norm = models.CharField(max_length=255, blank=True, null=True)
    org = models.CharField(max_length=255, blank=False, null=False)
    lemmatisierung = models.CharField(max_length=255, blank=False, null=True)
    filename = models.CharField(max_length=255, blank=True, null=False)
    count = models.IntegerField(default=0)

    comment = models.TextField(blank=True, help_text="Comment on Lemmata")

    simplex = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="complex_lemmata",
        verbose_name="Simplex",
        blank=True,
        null=True,
    )

    suggestion = models.CharField(max_length=255, blank=True, null=True)

    pos = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.norm


class Edit_of_article(models.Model):
    """Class to store tags for incoming elasticsearch documents"""

    begin_time = models.DateTimeField(editable=True, default=timezone.now)

    class StepChoices(Enum):
        ARTIKEL_IN_ARBEIT = "Artikel in Arbeit"
        ARTIKEL_ERSTELLT = "Artikel erstellt"
        LAUTKOMMENTAR_ERSTELLT = "Lautkommentar erstellt"
        LAUTKOMMENTAR_HINZUGEFÜGT = "Lautkommentar hinzugefügt"
        IRRELEVANT = "Irrelevant"
        FREIGEGEBEN_FUER_LK = "Freigegeben für Lautkommentar"
        FREIGEGEBEN_FUER_VORARBEITEN = "Freigegeben für Vorarbeiten"
        VERBREITUGS_COLLECTION_ERSTELLT = "Verbreitungs-Collection erstellt"
        ZUGEWIESEN = "Zugewiesen"

        @classmethod
        def choices(cls):
            return tuple((i.name, i.value) for i in cls)

    step = models.CharField(max_length=255, choices=StepChoices.choices())

    class StatusChoices(Enum):
        DRAFT = "draft"
        PEER_CORRECTION = "peer correction"
        INTERNAL_CORRECTION = "internal correction"
        EXTERNAL_CORRECTION = "external correction"
        ONLINE = "online"
        FINAL_VERSION = "final version"

        @classmethod
        def choices(cls):
            return tuple((i.name, i.value) for i in cls)

    status = models.CharField(max_length=255, choices=StatusChoices.choices())

    finished_date = models.DateTimeField(null=True, blank=False)

    description = models.TextField(blank=True, help_text="Comment on Edit of Article")

    current = models.BooleanField(
        default=False, help_text="Is this the current entry of the edit"
    )

    deadline = models.DateTimeField(null=True, blank=False)

    last_edited = models.DateTimeField(default=timezone.now, null=False, blank=False)

    user = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="article_edits",
        help_text="The user who did this editing",
    )

    lemma = models.ForeignKey(
        Lemma,
        blank=False,
        null=True,
        on_delete=models.SET_NULL,
        related_name="lemma",
        help_text="Assigned lemma to this edit",
    )

    def save(self, *args, **kwargs):
        self.last_edited = timezone.now()
        return super(Edit_of_article, self).save(*args, **kwargs)


class Collection(models.Model):
    """1 to n references to elasticsearch documents"""

    title = models.CharField(
        max_length=255,
        blank=True,
        help_text="Title",
        db_index=True,
    )
    description = models.TextField(
        blank=True, help_text="Describe the collection", verbose_name="Description"
    )
    created_by = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="collections_created",
        help_text="The user who created current collection",
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="collections",
        verbose_name="Category",
        blank=True,
        null=True,
        limit_choices_to=Q(
            name__in=[
                "distribution",
                "sense",
                "multi_word_expression",
                "etymology",
                "compound",
                "lemma",
            ]
        ),
    )

    lemma_id = models.ForeignKey(
        Lemma,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="of_collections",
        help_text="Collections in which this lemma apperas",
    )

    es_document = models.ManyToManyField(
        Es_document, related_name="in_collections", verbose_name="Document", blank=True
    )
    comment = models.TextField(blank=True, help_text="Comment on collection")
    curator = models.ManyToManyField(
        User,
        related_name="collections_curated",
        blank=True,
        help_text="The selected user(s) will be able to view, edit and delete current Collection.",
    )
    public = models.BooleanField(
        default=False, help_text="Public collection or not. By default is not public."
    )

    deleted = models.BooleanField(
        default=False,
        help_text="deletion flag",
        db_index=True,
    )

    created = models.DateTimeField(editable=False, default=timezone.now)
    modified = models.DateTimeField(editable=False, db_index=True, default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super(Collection, self).save(*args, **kwargs)

    def __str__(self):
        if self.title:
            return "{}".format(self.title)
        else:
            return "{}".format(self.id)

    @property
    def tags(self):
        return set([tag for x in self.es_document.all() for tag in x.tag.all()])


class Annotation(models.Model):
    title = models.CharField(max_length=255, blank=True, verbose_name="Title")
    collection = models.ForeignKey(
        Collection,
        on_delete=models.SET_NULL,
        related_name="annotations",
        verbose_name="Collection",
        blank=True,
        null=True,
    )
    description = models.TextField(
        blank=True, help_text="Describe the annotation", verbose_name="Description"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="annotations",
        verbose_name="Category",
        blank=True,
        null=True,
    )
    public = models.BooleanField(
        default=False, help_text="Public annotation or not. By default is not public."
    )
    created_by = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="annotations_created",
        help_text="The user who created current annotation",
    )
    created = models.DateTimeField(editable=False, default=timezone.now)
    modified = models.DateTimeField(editable=False, default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super(Annotation, self).save(*args, **kwargs)

    def __str__(self):
        return "{}".format(self.id)


class Autor_Artikel(models.Model):
    lemma_id = models.ForeignKey(
        Lemma,
        on_delete=models.SET_NULL,
        null=True,
        related_name="article_author_lemma",
        verbose_name="article_author_lemma",
    )

    bearbeiter_id = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,
        related_name="article_author",
        verbose_name="Artikel, die der Autor bearbeitet hat",
    )
