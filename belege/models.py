import xml.etree.ElementTree as ET

from acdh_tei_pyutils.tei import TeiReader
from acdh_tei_pyutils.utils import get_xmlid
from django.db import models
from django.db.models import Index, Q
from django_jsonform.models.fields import ArrayField, JSONField

from annotations.models import Collection, Tag
from belege.fields import XMLField
from belege.opensearch_client import OS_CONNECTION, OS_INDEX_NAME, client
from belege.utils import annotate_text, populate_fields_from_xml, transform_record
from siglen.models import BelegSigle

ref_type_filter = " or ".join(
    f"@type = '{ref_type}'"
    for ref_type in (
        "seite",
        "paragraph",
        "karte",
        "dbo",
        "sni",
        "sna",
        "quelleDetaillierte",
        "quelleNeu",
        "quelleZitierte",
    )
)
REF_BELGE_XPATH = f"./tei:ref[{ref_type_filter}]"

POS_CHOICES = (
    ("Subst", "Substantiv"),
    ("Interj", "Interjektion"),
    ("Verb", "Verb"),
    ("Adj", "Adjektiv"),
    ("Pron", "Pronomen"),
    ("Adv", "Adverb"),
    ("Prep", "Präposition"),
    ("Conj", "Konjunktion"),
    ("Num", "Numeral"),
)

LANG_CHOICES = (("bar", "bar"), ("de", "de"))

RESP_OPTIONS = (("O", "O"), ("B", "B"))

REFS_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "corresp": {"type": "string"},
            "type": {"type": "string"},
            "text": {"type": "string"},
            "bibl": {"type": "array", "items": {"type": "string"}},
        },
        "additionalProperties": True,
    },
}

NOTES_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "n": {"type": "string"},
            "ref": {"type": "string"},
            "corresp": {"type": "string"},
            "type": {"type": "string"},
            "subtype": {"type": "string"},
            "resp": {"type": "string"},
            "text": {"type": "string"},
            "pRef": {"type": "array", "items": {"type": "string"}},
        },
        "additionalProperties": True,
    },
}

XR_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "corresp": {"type": "string"},
            "type": {"type": "string"},
            "resp": {"type": "string"},
            "text": {"type": "string"},
            "pRef": {"type": "array", "items": {"type": "string"}},
        },
        "additionalProperties": True,
    },
}

ETYMOLOGY_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "n": {"type": "string"},
            "corresp": {"type": "string"},
            "text": {"type": "string"},
            "pRef": {"type": "string"},
            "ref__type_paragraph": {"type": "string"},
            "note__resp_B__type_anmerkung": {"type": "string"},
            "resp": {"type": "string"},
        },
        "additionalProperties": True,
    },
}

DEF_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "n": {"type": "string"},
            "corresp": {"type": "string"},
            "lang": {"type": "string"},
            "text": {"type": "string"},
            "pRef": {"type": "string"},
            "resp": {"type": "string"},
        },
        "additionalProperties": True,
    },
}

RE_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "text": {"type": "string"},
            "type": {"type": "string"},
            "form": {"type": "array", "items": {"type": "string"}},
            "gramGrp": {"type": "array", "items": {"type": "string"}},
        },
        "additionalProperties": True,
    },
}


def set_extra(self, **kwargs):
    self.extra = kwargs
    return self


models.Field.set_extra = set_extra


class Citation(models.Model):
    """
    Django model representing a citation (Kontext) extracted from TEI XML documents.
    """

    dboe_id = models.CharField(
        primary_key=True,
        max_length=250,
        verbose_name="DBÖ ID",
        help_text="e.g. tu-10130.56",
    )
    beleg = models.ForeignKey(
        "Beleg",
        verbose_name="Beleg",
        on_delete=models.CASCADE,
        related_name="citations",
    )
    number = models.PositiveIntegerField(default=1, verbose_name="order number")
    quote_lang = models.CharField(
        max_length=3,
        choices=LANG_CHOICES,
        blank=True,
        null=True,
        verbose_name="Sprache (Kontext)",
    ).set_extra(xpath="./tei:quote/@xml:lang", node_type="attribute")
    quote_text = models.TextField(
        blank=True,
        null=True,
        verbose_name="Kontext",
        help_text="No help text provided",
    ).set_extra(xpath="./tei:quote", node_type="text")
    quote_gram = models.CharField(
        max_length=250,
        blank=True,
        null=True,
        verbose_name="Grammatik",
        help_text="whatever",
    ).set_extra(xpath="./tei:quote/tei:seg[@type='gram']", node_type="text")
    p_ref = models.CharField(
        blank=True,
        null=True,
        verbose_name="Pronunciation reference",
        help_text="whatever",
    ).set_extra(xpath="./tei:quote/tei:pRef", node_type="text")
    definition_node = JSONField(
        blank=True,
        null=True,
        verbose_name="Bedeutung des Kontexts (tei:def)",
        help_text='Diese Information beschreibt die Bedeutung des in Spalte "Belegsatz 1", "Belegsatz 2" etc. angegebenen Belegsatze',  # noqa: E501
        schema=DEF_SCHEMA,
    ).set_extra(xml_element="./tei:def")
    corresp = models.CharField(
        max_length=250,
        blank=True,
        null=True,
        verbose_name="Korrespondiert zu",
    ).set_extra(xpath="./@corresp", node_type="attribute")
    interpration = models.TextField(
        blank=True,
        null=True,
        verbose_name="interpretation",
        help_text="Summarizes a specific interpretative annotation which can be linked to a span of text",
    ).set_extra(xpath="./tei:interp", node_type="text")
    fragebogen_nummer = models.TextField(
        blank=True,
        null=True,
        verbose_name="Fragebogen Nummer",
        help_text="Whatever",
    ).set_extra(xpath="./tei:ref[@type='fragebogenNummer']", node_type="text")
    note = JSONField(
        blank=True,
        null=True,
        verbose_name="tei:note",
        help_text="stores any kind of ./tei:note",
        schema=NOTES_SCHEMA,
    ).set_extra(xml_element="./tei:note")
    xr_node = JSONField(
        blank=True,
        null=True,
        verbose_name="tei:xr",
        help_text="stores any kind of ./tei:xr",
        schema=XR_SCHEMA,
    ).set_extra(xml_element="./tei:xr")
    re_node = JSONField(
        blank=True,
        null=True,
        verbose_name="tei:re",
        help_text="Zusatzlemma",
        schema=RE_SCHEMA,
    ).set_extra(xml_element="./tei:re")

    class Meta:
        verbose_name = "Kontext"
        verbose_name_plural = "Kontexte"
        ordering = ["beleg", "number"]

    def save(self, orig_xml=None, *args, **kwargs):
        xml_source = orig_xml
        if xml_source is not None:
            try:
                doc = TeiReader(xml_source)
            except AttributeError:
                doc = TeiReader(ET.tostring(xml_source).decode("utf-8"))
            populate_fields_from_xml(doc, self)
        super().save(*args, **kwargs)


class Annotation(models.Model):
    kontext = models.ForeignKey(
        "Citation",
        verbose_name="Kontext",
        on_delete=models.CASCADE,
        related_name="annotation",
    )
    payload = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Annotated text",
        help_text="stores result of NLP processing",
    )
    tool = models.CharField(
        blank=True, null=True, verbose_name="Tool/Model used to process the data"
    )
    source_field = models.CharField(
        default="quote_text",
        max_length=250,
        verbose_name="Source field",
        help_text="name of the field, the annotated text was derived from",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Annotation"
        verbose_name_plural = "Annotations"
        ordering = ["kontext", "created_at"]

    def __str__(self):
        return f"Annotation for {self.kontext.dboe_id} using {self.tool}"


class Lautung(models.Model):
    """
    Django model representing a tei:form[@type="lautung"] node.
    """

    dboe_id = models.CharField(
        primary_key=True,
        max_length=250,
        verbose_name="DBÖ ID",
        help_text="e.g. tu-112119.52",
    )
    beleg = models.ForeignKey(
        "Beleg",
        verbose_name="Beleg",
        on_delete=models.CASCADE,
        related_name="lautungen",
    )
    number = models.PositiveIntegerField(default=1, verbose_name="Order number")
    pron = models.CharField(
        blank=True,
        null=True,
        max_length=250,
        verbose_name="Lautung",
        help_text="Die angegebene Information umfasst die lautliche Transkription des vorliegenden Belegs.",
    ).set_extra(xpath="./tei:pron", node_type="text")
    pron_lang = models.CharField(
        max_length=3,
        choices=LANG_CHOICES,
        blank=True,
        null=True,
        verbose_name="Sprache (Lautung)",
        help_text="No help text provided",
    ).set_extra(xpath="./tei:pron/@xml:lang", node_type="attribute")
    pron_gram = models.CharField(
        blank=True,
        null=True,
        max_length=250,
        verbose_name="Grammatikangabe zur Lautung",
        help_text="No help text provided",
    ).set_extra(xpath="./tei:gramGrp/tei:gram", node_type="text")

    class Meta:
        verbose_name = "Lautung"
        verbose_name_plural = "Lautungen"
        ordering = ["beleg", "number"]

    def __str__(self):
        return f"{self.pron} ({self.beleg})"

    def save(self, orig_xml=None, *args, **kwargs):
        xml_source = orig_xml
        if xml_source is not None:
            try:
                doc = TeiReader(xml_source)
            except AttributeError:
                doc = TeiReader(ET.tostring(xml_source).decode("utf-8"))
            populate_fields_from_xml(doc, self)
        super().save(*args, **kwargs)


class LehnWort(models.Model):
    """
    Django model representing a tei:form[@type="lehnwort"] node.
    """

    dboe_id = models.CharField(
        primary_key=True,
        max_length=250,
        verbose_name="DBÖ ID",
        help_text="e.g. tu-112.38",
    )
    beleg = models.ForeignKey(
        "Beleg",
        verbose_name="Beleg",
        on_delete=models.CASCADE,
        related_name="lehnwoerter",
    )
    number = models.PositiveIntegerField(default=1, verbose_name="Order number")
    pron = models.CharField(
        blank=True,
        null=True,
        max_length=250,
        verbose_name="Lehnwort",
        help_text="no help text provided",
    ).set_extra(xpath="./tei:pron", node_type="text")
    pron_lang = models.CharField(
        max_length=3,
        choices=LANG_CHOICES,
        blank=True,
        null=True,
        verbose_name="Sprache (Pronunciation)",
    ).set_extra(xpath="./tei:pron/@xml:lang", node_type="attribute")
    pron_gram = models.CharField(
        blank=True,
        null=True,
        max_length=250,
        verbose_name="Grammatik",
        help_text="whatever",
    ).set_extra(xpath="./tei:gramGrp/tei:gram", node_type="text")

    class Meta:
        verbose_name = "Lehnwort"
        verbose_name_plural = "Lehnwörter"
        ordering = ["beleg", "number"]

    def __str__(self):
        return f"{self.pron} ({self.beleg})"

    def save(self, orig_xml=None, *args, **kwargs):
        xml_source = orig_xml
        if xml_source is not None:
            try:
                doc = TeiReader(xml_source)
            except AttributeError:
                doc = TeiReader(ET.tostring(xml_source).decode("utf-8"))
            populate_fields_from_xml(doc, self)
        super().save(*args, **kwargs)


class Sense(models.Model):
    """
    Django model representing a tei:sense node.
    """

    dboe_id = models.CharField(
        primary_key=True,
        max_length=250,
        verbose_name="DBÖ ID",
        help_text="e.g. tu-10130.56",
    )
    beleg = models.ForeignKey(
        "Beleg",
        verbose_name="Beleg",
        on_delete=models.CASCADE,
        related_name="bedeutungen",
    )
    number = models.PositiveIntegerField(default=1, verbose_name="Order number")
    definition = models.TextField(
        blank=True,
        null=True,
        verbose_name="Bedeutung der Lautung",
        help_text="Diese Information beschreibt die Bedeutung der Lautungsangabe auf dem Beleg.",
    ).set_extra(xpath="./tei:def", node_type="text")
    corresp_to = models.CharField(
        blank=True, null=True, max_length=20, verbose_name="Korrespondiert zu"
    ).set_extra(xpath="./@corresp", node_type="attribute")
    definition_lang = models.CharField(
        max_length=3,
        choices=LANG_CHOICES,
        blank=True,
        null=True,
        verbose_name="Sprache (Definition)",
    ).set_extra(xpath="./tei:def/@xml:lang", node_type="attribute")
    note = JSONField(
        blank=True,
        null=True,
        verbose_name="tei:note",
        help_text="stores any kind of ./tei:note",
        schema=NOTES_SCHEMA,
    ).set_extra(xml_element="./tei:note")

    class Meta:
        verbose_name = "Bedeutung"
        verbose_name_plural = "Bedeutungen"
        ordering = ["beleg", "number"]

    def __str__(self):
        return f"{self.definition[:25]} ... ({self.beleg})"

    def save(self, orig_xml=None, *args, **kwargs):
        xml_source = orig_xml
        if xml_source is not None:
            try:
                doc = TeiReader(xml_source)
            except AttributeError:
                doc = TeiReader(ET.tostring(xml_source).decode("utf-8"))
            populate_fields_from_xml(doc, self)
        super().save(*args, **kwargs)


class BelegManager(models.Manager):
    def with_related(self):
        """Return queryset with all related objects prefetched for optimal performance."""

        return self.select_related("quelle_type").prefetch_related(
            "citations",
            "lautungen",
            "lehnwoerter",
            "bedeutungen",
            "tag",
            models.Prefetch(
                "belegsigle_set",
                queryset=BelegSigle.objects.select_related(
                    "sigle", "sigle__bl", "sigle__gr", "sigle__kr"
                ),
            ),
        )


class Beleg(models.Model):
    """
    A Beleg entry from the DBÖ (Dictionary of Bavarian Dialects in Austria) database.
    """

    dboe_id = models.CharField(
        primary_key=True,
        max_length=250,
        verbose_name="Beleg ID",
        help_text="No help text provided",
    )
    orig_xml = XMLField(blank=True, null=True, verbose_name="original tei-xml entry")
    xeno_data = models.TextField(
        blank=True, null=True, verbose_name="legacy transkription?"
    )
    hauptlemma = models.CharField(
        blank=True,
        null=True,
        max_length=250,
        verbose_name="Hauptlemma",
        help_text="Hauptlemma' beinhaltet sämtliche Einträge (inklusive Komposita und Wortbildungsvarianten), die einem bestimmten Lemma zugeordnet werden können",  # noqa: E501
    ).set_extra(xpath="./tei:form[@type='hauptlemma'][1]/tei:orth", node_type="text")
    hauptlemma_norm = models.CharField(
        blank=True,
        null=True,
        max_length=260,
        verbose_name="Hauptlemma (normalisiert)",
        help_text="Normalisiertes Hauptlemma",
    )
    nebenlemma = models.CharField(
        blank=True,
        null=True,
        max_length=250,
        verbose_name="Nebenlemma",
        help_text="Ein Nebenlemma ist einem Hauptlemma zugeordnet. Das Nebenlemma teilt sich mit dem übergeordneten Hauptlemma (in weiten Teilen) den historisch-etymologischen Lemmaansatz, kann jedoch in anderer Hinsicht (z.B. Schreibung, Lautung) vom Hauptlemma abweichen.",  # noqa: E501
    ).set_extra(xpath="./tei:form[@type='nebenlemma']/tei:orth", node_type="text")
    archivzeile = models.CharField(
        blank=True,
        null=True,
        max_length=250,
        verbose_name="Archivzeile",
        help_text="No helptext provided",
    ).set_extra(xpath="./tei:ref[@type='archiv']", node_type="text")
    quelle = models.CharField(
        blank=True,
        null=True,
        max_length=250,
        verbose_name="Quelle",
        help_text="No helptext provided",
    ).set_extra(xpath="./tei:ref[@type='quelle']", node_type="text")
    quelle_page = models.CharField(
        blank=True, null=True, max_length=250, verbose_name="Seite"
    ).set_extra(
        xpath="./tei:ref[@type='quelle']/tei:ref[@type='seite']",
        node_type="text",
        help_text="No helptext provided",
    )
    quelle_bearbeitet = models.CharField(
        blank=True, null=True, max_length=250, verbose_name="Quelle bearbeitet"
    ).set_extra(
        xpath="./tei:ref[@type='quelleBearbeitet']",
        node_type="text",
        help_text="No helptext provided",
    )
    bibl = models.CharField(
        blank=True,
        null=True,
        max_length=250,
        verbose_name="Literatur",
        help_text="No helptext provided",
    ).set_extra(xpath="./tei:ref[@type='bibl']/tei:bibl", node_type="text")
    zitierweise = ArrayField(
        models.CharField(blank=True, max_length=250, null=True),
        blank=True,
        default=list,
        verbose_name="Zitierweise",
        help_text="No helptext provided",
    ).set_extra(xpath="./tei:ref[@type='zitiereweise']/tei:bibl", node_type="list")
    scan = ArrayField(
        models.CharField(blank=True, max_length=350, null=True),
        blank=True,
        default=list,
        verbose_name="Scans",
        help_text="Scans",
    ).set_extra(xpath="./@facs", node_type="list")
    year = models.CharField(
        blank=True,
        null=True,
        max_length=250,
        verbose_name="Jahr",
        help_text="No helptext provided",
    ).set_extra(
        xpath="tei:ref[@type='quelle']/tei:ref[@type='date']/tei:date", node_type="text"
    )
    pos = models.CharField(
        blank=True,
        null=True,
        max_length=20,
        verbose_name="Part of Speech",
        help_text="Diese Angabe benennt die Wortart des jeweiligen Belegs.",
        choices=POS_CHOICES,
    ).set_extra(xpath="./tei:gramGrp/tei:pos", node_type="text")
    fragebogen_nummer = models.TextField(
        blank=True,
        null=True,
        verbose_name="Fragebogen Nummer",
        help_text="Whatever",
    ).set_extra(xpath="./tei:ref[@type='fragebogenNummer']", node_type="text")
    etymology = JSONField(
        blank=True,
        null=True,
        verbose_name="Etymologie",
        help_text="whatever",
        schema=ETYMOLOGY_SCHEMA,
    ).set_extra(xml_element="./tei:etym")
    place_qu = ArrayField(
        models.CharField(blank=True, max_length=250, null=True),
        blank=True,
        default=list,
        verbose_name="Ort (QU)",
        help_text="No helptext provided",
    ).set_extra(xpath="./tei:usg[@corresp='this:QU']/tei:placeName", node_type="list")
    place_qdb = ArrayField(
        models.CharField(blank=True, max_length=250, null=True),
        blank=True,
        default=list,
        verbose_name="Ort (QDB)",
        help_text="No helptext provided",
    ).set_extra(xpath="./tei:usg[@corresp='this:QDB']/tei:placeName", node_type="list")
    import_issue = models.BooleanField(
        default=False,
        verbose_name="Import issue",
        help_text="Set to True if there was an issue during import",
    )
    tag = models.ManyToManyField(
        Tag,
        related_name="belege",
        blank=True,
        verbose_name="Tag",
    )
    collection = models.ManyToManyField(
        Collection,
        blank=True,
        verbose_name="Collection",
        help_text="Collection",
        related_name="beleg",
    )
    sigle = models.ManyToManyField(
        "siglen.Sigle", blank=True, verbose_name="Sigle", through="siglen.BelegSigle"
    )
    quelle_type = models.ForeignKey(
        "bibls.BibliographicType",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    internal_comment = models.TextField(
        blank=True,
        null=True,
        verbose_name="interne Kommentare",
        help_text="Feld für interne Anmerkungen",
    )
    has_scan = models.BooleanField(default=False)
    has_internal_comment = models.BooleanField(default=False)
    note = JSONField(
        blank=True,
        null=True,
        verbose_name="tei:note",
        help_text="stores any kind of ./tei:note",
        schema=NOTES_SCHEMA,
    ).set_extra(xml_element="./tei:note")
    xr = JSONField(
        blank=True,
        null=True,
        verbose_name="tei:xr",
        help_text="stores any kind of ./tei:xr",
        schema=XR_SCHEMA,
    ).set_extra(xml_element="./tei:xr")
    ref = JSONField(
        blank=True,
        null=True,
        verbose_name="tei:ref",
        help_text="stores tei:ref with different @type values",
        schema=REFS_SCHEMA,
    ).set_extra(xml_element=REF_BELGE_XPATH)

    objects = BelegManager()

    class Meta:
        verbose_name = "Beleg"
        verbose_name_plural = "Belege"
        ordering = ["dboe_id"]
        indexes = [
            Index(
                name="beleg_has_scan_true_idx",
                fields=["dboe_id"],
                condition=Q(has_scan=True),
            ),
            Index(
                name="beleg_has_comment_true_idx",
                fields=["dboe_id"],
                condition=Q(has_internal_comment=True),
            ),
        ]

    def __str__(self):
        if self.hauptlemma:
            return f"{self.dboe_id} ({self.hauptlemma})"
        return f"{self.dboe_id}"

    def save(
        self,
        add_citations=False,
        add_lautungen=False,
        add_sense=False,
        add_lehnwort=False,
        trigger_index=True,
        *args,
        **kwargs,
    ):
        xml_source = self.orig_xml
        if xml_source is not None:
            self.import_issue = False
            try:
                doc = TeiReader(xml_source)
            except AttributeError:
                doc = TeiReader(ET.tostring(xml_source).decode("utf-8"))
            populate_fields_from_xml(doc, self)
        if xml_source is not None and add_citations:
            items = doc.any_xpath("./tei:cit")
            for n, item in enumerate(items, start=1):
                try:
                    xml_id = get_xmlid(item)
                except KeyError:
                    xml_id = f"tu-cit-{self.dboe_id}_{n:0>2}"
                try:
                    number = item.attrib["n"]
                except KeyError:
                    number = n
                item_orig_xml = ET.tostring(item, encoding="unicode")
                try:
                    item = Citation.objects.get(dboe_id=xml_id)
                except Citation.DoesNotExist:
                    item = Citation(
                        dboe_id=xml_id,
                        beleg=self,
                        number=number,
                    )
                try:
                    item.save(orig_xml=item_orig_xml)
                except Exception as e:
                    print(f"Error saving citation {xml_id}: {e}")
        if xml_source is not None and add_lautungen:
            items = doc.any_xpath("./tei:form[@type='lautung']")
            for n, item in enumerate(items, start=1):
                try:
                    xml_id = get_xmlid(item)
                except KeyError:
                    xml_id = f"tu-lt-{self.dboe_id}_{n:0>2}"
                try:
                    number = item.attrib["n"]
                except KeyError:
                    number = 1
                item_orig_xml = ET.tostring(item, encoding="unicode")
                try:
                    item = Lautung.objects.get(dboe_id=xml_id)
                except Lautung.DoesNotExist:
                    item = Lautung(
                        dboe_id=xml_id,
                        beleg=self,
                        number=number,
                    )
                try:
                    item.save(orig_xml=item_orig_xml)
                except Exception as e:
                    print(f"Error saving lautung {xml_id}: {e}")
        if xml_source is not None and add_lehnwort:
            items = doc.any_xpath("./tei:form[@type='lehnwort']")
            for n, item in enumerate(items, start=1):
                try:
                    xml_id = get_xmlid(item)
                except KeyError:
                    xml_id = f"tu-lw-{self.dboe_id}_{n:0>2}"
                try:
                    number = item.attrib["n"]
                except KeyError:
                    number = 1
                item_orig_xml = ET.tostring(item, encoding="unicode")
                try:
                    item = LehnWort.objects.get(dboe_id=xml_id)
                except LehnWort.DoesNotExist:
                    item = LehnWort(
                        dboe_id=xml_id,
                        beleg=self,
                        number=number,
                    )
                try:
                    item.save(orig_xml=item_orig_xml)
                except Exception as e:
                    print(f"Error saving LehnWort {xml_id}: {e}")
        if xml_source is not None and add_sense:
            items = doc.any_xpath("./tei:sense")
            for n, item in enumerate(items, start=1):
                try:
                    xml_id = get_xmlid(item)
                except KeyError:
                    xml_id = f"tu-lw-{self.dboe_id}_{n:0>2}"
                number = n
                item_orig_xml = ET.tostring(item, encoding="unicode")
                try:
                    item = Sense.objects.get(dboe_id=xml_id)
                except Sense.DoesNotExist:
                    item = Sense(
                        dboe_id=xml_id,
                        beleg=self,
                        number=number,
                    )
                try:
                    item.save(orig_xml=item_orig_xml)
                except Exception as e:
                    print(f"Error saving sense {xml_id}: {e}")
        self.has_scan = bool(self.scan)
        self.has_internal_comment = bool(self.internal_comment)
        if OS_CONNECTION and trigger_index:
            document = self.sanitize_representation()
            id = document["id"]
            client.index(index=OS_INDEX_NAME, body=document, id=id, refresh=True)

        super().save(*args, **kwargs)

    def build_representation(self, base: dict | None = None) -> dict:
        """Return a dict identical to ``BelegSerializer.to_representation``."""

        # Build the initial base if none was provided
        if base is None:
            base = {
                "id": self.dboe_id,
                "hl": self.hauptlemma,
                "hl_norm": self.hauptlemma_norm,
                "nl": self.nebenlemma,
                "qu": self.quelle,
                "qdb": self.quelle_bearbeitet,
                "bibl": self.bibl,
                "year": self.year,
                "pos": self.pos,
                "archivzeile": self.archivzeile,
                "internal_comment": self.internal_comment,
            }

        ret = dict(base)  # copy so we don't mutate caller provided dict
        if self.quelle_type:
            ret["quelle_type_main"] = self.quelle_type.main_type
            ret["quelle_type_sub"] = self.quelle_type.sub_type
            ret["quelle_type_specific"] = self.quelle_type.specification
        else:
            ret["quelle_type_main"] = ""
            ret["quelle_type_sub"] = ""
            ret["quelle_type_specific"] = ""

        # Collect simple references
        ret["tustep"] = self.xeno_data
        ret["scans"] = self.scan

        # process notes
        ret["div"] = []  # "DIV" : $e/tei:note[@type="diverse"and @n="1"]
        ret[
            "anm_lt_star"
        ] = []  # "ANM/LT*": $e/tei:note[@type="anmerkung" and @corresp=("this:LT1",...", "this:LT10")],
        ret[
            "anm_lw_star"
        ] = []  # "ANM/LW*": $e/tei:note[@type="anmerkung" and @corresp=("this:LW1",... "this:LW8")],
        ret[
            "dv_lw_star"
        ] = []  # "DV/LW*": $e/tei:note[@type="diverse" and @corresp=("this:LW1", ..., "this:LW8")],
        ret[
            "anm"
        ] = []  # $e/tei:note[@type=("anmerkung", "notabene") and not(starts-with(@corresp, "this:L"))],
        if self.note:
            for x in self.note:
                corresp = x.get("corresp") or ""
                resp = x.get("resp") or ""
                if resp:
                    resp = f"{resp}: "
                if x.get("type") == "diverse" and x.get("n") == "1" and x.get("text"):
                    return_value = x.get("text")
                    return_value = annotate_text(return_value, x.get("pRef"))
                    ret["div"].append(return_value)
                if x.get("type") == "anmerkung" and "this:LT" in corresp:
                    return_value = f"{resp}{x.get('text')} ›{corresp}"
                    return_value = annotate_text(return_value, x.get("pRef"))
                    ret["anm_lt_star"].append(return_value)
                if x.get("type") == "anmerkung" and "this:LW" in corresp:
                    return_value = f"{resp}{x.get('text')} ›{corresp}"
                    return_value = annotate_text(return_value, x.get("pRef"))
                    ret["anm_lw_star"].append(return_value)
                if x.get("type") == "diverse" and "this:LW" in corresp:
                    return_value = f"{resp}{x.get('text')} ›{corresp}"
                    return_value = annotate_text(return_value, x.get("pRef"))
                    ret["dv_lw_star"].append(return_value)
                if (
                    x.get("type")
                    in [
                        "anmerkung",
                        "notabene",
                    ]
                    and "this:L" not in corresp
                ):
                    ret["anm"].append(f"{resp}{x.get('text')}")

        # verweise "Verweis": $e/(tei:ref,tei:xr)[@type=("verweise", "sni", "dbo")]
        verweise = []
        verweis_types = ["verweise", "sni", "dbo", "sna"]
        ret["quelle_detaillierte"] = []
        ret["quelle_neu"] = []
        ret["quelle_zitiert"] = []
        if self.xr:
            for x in self.xr:
                resp = x.get("resp") or ""
                if resp:
                    resp = f"{resp}: "
                corresp = x.get("corresp") or ""
                if corresp:
                    corresp = f" ›{corresp}"
                node_type = x.get("type") or ""
                if node_type in verweis_types:
                    verweise.append(f"{resp}{x.get('text')}{corresp}")
        if self.ref:
            for x in self.ref:
                corresp = x.get("corresp") or ""
                if corresp:
                    corresp = f" ›{corresp}"
                node_type = x.get("type") or ""
                if node_type in verweis_types:
                    verweise.append(f"{x.get('text')}{corresp}")
                if node_type == "quelleDetaillierte":
                    ret["quelle_detaillierte"].append(f"{x.get('text')}{corresp}")
                if node_type == "quelleNeu":
                    ret["quelle_neu"].append(f"{x.get('text')}{corresp}")
                if node_type == "quelleZitierte":
                    ret["quelle_zitiert"].append(f"{x.get('text')}{corresp}")

        ret["etym"] = []  # $e/tei:etym
        if self.etymology:
            for x in self.etymology:
                corresp = x.get("corresp") or ""
                resp = x.get("resp") or ""
                ret["etym"].append(f"{resp}: {x.get('text')}")

        try:
            cit_fragebogen_nr = " ".join(
                c.fragebogen_nummer for c in self.citations.all() if c.fragebogen_nummer
            )
        except TypeError:
            cit_fragebogen_nr = ""
        if self.fragebogen_nummer:
            fragebogen_nr = f"{self.fragebogen_nummer} "
        else:
            fragebogen_nr = ""
        ret["nr"] = f"{fragebogen_nr}{cit_fragebogen_nr}"
        ret["verweis"] = verweise
        ret["page"] = self.quelle_page

        ret["a"] = self.archivzeile
        ret["tags"] = [x.name for x in self.tag.all()]

        ret["ort"] = []
        [ret["ort"].append(x) for x in self.place_qu]
        [ret["ort"].append(x) for x in self.place_qdb]

        siglen = set()
        bundeslaender = set()
        gregion = set()
        kregion = set()
        orig_orte = list()
        for x in self.belegsigle_set.all():
            siglen.add(x.sigle.sigle)
            try:
                bundeslaender.add(getattr(x.sigle, "bl"))
            except AttributeError:
                pass
            try:
                gregion.add(getattr(x.sigle, "gr"))
            except AttributeError:
                pass
            try:
                kregion.add(getattr(x.sigle, "kr"))
            except AttributeError:
                pass
        ret["siglen"] = list(siglen)
        ret["bundeslaender"] = [f"{x.name} ({x.sigle})" for x in bundeslaender if x]
        ret["gregion"] = [f"{x.name} ({x.sigle})" for x in gregion if x]
        ret["kregion"] = [f"{x.name} ({x.sigle})" for x in kregion if x]
        ret["orig_orte"] = orig_orte

        # Lautungen
        for x in self.lautungen.all():
            gram_key = f"gram_lt{x.number}"
            value = getattr(x, "pron_gram")
            ret[gram_key] = value
            teut_key = f"lt{x.number}_teuthonista"
            ret[teut_key] = x.pron

        # Lehnwörter
        for x in self.lehnwoerter.all():
            number = x.number
            ret[f"lw{number}"] = x.pron

        # Use prefetched citations
        citations_list = list(self.citations.all())
        try:
            first_citation = next((c for c in citations_list if c.number == 1), None)
            if first_citation:
                ret["kl_kt1"] = first_citation.interpration
        except AttributeError:
            pass

        ret["anm_kt_star"] = []
        ret["bd_kt_star"] = []
        ret["wbd_kt_star"] = []
        ret["vrw_kt_star"] = []
        ret[
            "dv_kt_star"
        ] = []  # "DV/KT*" : $e/tei:cit[@type="kontext"]/tei:note[@type="diverse"]

        for x in citations_list:
            if (
                x.corresp and "this:LT" in x.corresp
            ):  # "KT/LT1" : $e/tei:cit[@type = "kontext"][@corresp = "this:LT1"]/tei:quote[1],
                cur_lt = x.corresp.split(":")[-1]
                key = f"kt_{cur_lt.lower()}"
                value = x.quote_text
                ret[key] = value
            if x.definition_node:
                for y in x.definition_node:
                    corresp = f" {y.get('corresp')}" or ""
                    if y.get("corresp") and y.get("text"):
                        return_value = f"{y['text']} ›{corresp}"
                        return_value = annotate_text(return_value, y.get("pRef"))
                        ret["wbd_kt_star"].append(return_value)
                    if not y.get("corresp") and y.get("text"):
                        return_value = f"{y['text']} ›KT{x.number}"
                        return_value = annotate_text(return_value, y.get("pRef"))
                        ret["bd_kt_star"].append(return_value)
            ret[f"kt{x.number}"] = [x.quote_text]
            if x.note:
                for y in x.note:
                    resp = y.get("resp") or ""
                    if resp:
                        resp = f"{resp}: "
                    corresp = y.get("corresp") or ""
                    if corresp:
                        corresp = f"{corresp}/"
                    if y.get("text") and y.get("type") == "anmerkung":
                        return_value = (
                            f"{resp}{y['text']} ›{corresp}KT{x.number}".strip()
                        )
                        return_value = annotate_text(return_value, y.get("pRef"))
                        ret["anm_kt_star"].append(return_value)
                    if y.get("text") and y.get("type") == "diverse":
                        return_value = (
                            f"{resp}{y['text']} ›{corresp}KT{x.number}".strip()
                        )
                        return_value = annotate_text(return_value, y.get("pRef"))
                        ret["dv_kt_star"].append(return_value)
            if x.xr_node:
                for y in x.xr_node:
                    resp = y.get("resp") or ""
                    if resp:
                        resp = f"{resp}: "
                    ret["vrw_kt_star"].append(f"{resp}{y.get('text')} ›KT{x.number}")
            # ZL{nr}/KT{nr}: ZL1/KT1" : $e/tei:cit[@type="kontext" and @n="1"]/tei:re[@type="zusatzlemma"][1]
            if x.re_node:
                cur_nr = x.number
                for i, y in enumerate(x.re_node, start=1):
                    node_type = y.get("type") or ""
                    if node_type == "zusatzlemma":
                        cur_key = f"zl{i}_kt{cur_nr}"
                        ret[cur_key] = y.get("text")

        # Use prefetched bedeutungen - filter in Python
        # BD/LW* $e/tei:sense[@corresp=("this:LW1", "this:LW2", ..., "this:LW8")],
        bedeutungen_list = list(self.bedeutungen.all())
        ret["bd_lw_star"] = [
            annotate_text(f"{b.definition} ›{b.corresp_to}", [])
            for b in bedeutungen_list
            if b.corresp_to and "LW" in b.corresp_to
        ]

        # Filter bedeutungen in Python
        ret["bd_lt_star"] = []
        for x in bedeutungen_list:
            if x.corresp_to and "LT" in x.corresp_to:
                if x.note:
                    for y in x.note:
                        return_value = f"{x.definition} ANM{y.get('resp')}: {y.get('text')} ›{x.corresp_to}"
                        return_value = annotate_text(return_value, y.get("pRef"))
                        ret["bd_lt_star"].append(return_value)
                else:
                    return_value = f"{x.definition} ›{x.corresp_to}"
                    return_value = annotate_text(return_value, [])
                    ret["bd_lt_star"].append(return_value)

        for i, x in enumerate(self.zitierweise, start=1):
            ret[f"zw{i}"] = [x]
        return ret

    def sanitize_representation(self):
        raw = self.build_representation()
        processed = transform_record(raw)
        return processed
