import xml.etree.ElementTree as ET

from acdh_tei_pyutils.tei import TeiReader
from acdh_tei_pyutils.utils import extract_fulltext, get_xmlid
from acdh_xml_pyutils.xml import NSMAP
from django.db import models
from django_jsonform.models.fields import ArrayField

from annotations.models import Collection, Tag
from belege.fields import XMLField
from belege.opensearch_client import OS_CONNECTION, OS_INDEX_NAME, client
from belege.utils import transform_record

POS_CHOICES = (
    ("Subst", "Subst"),
    ("Interj", "Interj"),
    ("Verb", "Verb"),
    ("Adj", "Adj"),
)

LANG_CHOICES = (("bar", "bar"), ("de", "de"))

RESP_OPTIONS = (("O", "O"), ("B", "B"))


def set_extra(self, **kwargs):
    self.extra = kwargs
    return self


models.Field.set_extra = set_extra


class Facsimile(models.Model):
    """
    A facsimile
    """

    file_name = models.CharField(
        max_length=250, unique=True, verbose_name="Dateiname", help_text="whatever"
    )

    def sanitize_file_name(self):
        return self.file_name.replace("%2F", "/")

    @classmethod
    def get_base_url(cls):
        return "https://walk-want-grew-imgs.acdh-dev.oeaw.ac.at/iiif/images/"

    @property
    def facs_url(self):
        return f"{self.get_base_url()}{self.sanitize_file_name()}/info.json"

    @property
    def preview_url(self):
        return (
            f"{self.get_base_url()}{self.sanitize_file_name()}/full/600,/0/default.jpg"
        )

    def __str__(self):
        return self.preview_url

    class Meta:
        verbose_name = "Faksimile"
        verbose_name_plural = "Faksimiles"
        ordering = ["file_name"]


class ZusatzLemma(models.Model):
    """
    Django model representing a tei:re node extracted from a tei:cit node.
    """

    dboe_id = models.CharField(
        primary_key=True,
        max_length=250,
        verbose_name="DBÖ ID",
        help_text="e.g. tu-10130.56",
    )
    citation = models.ForeignKey(
        "Citation",
        verbose_name="Citation",
        on_delete=models.CASCADE,
        related_name="zusatz_lemma",
    )
    number = models.PositiveIntegerField(default=1, verbose_name="Order number")
    orig_xml = XMLField(
        verbose_name="XML Node", help_text="tei:form[@type='lautung'] node"
    )
    form_orth = models.CharField(
        blank=True, null=True, max_length=250, verbose_name="Lemma"
    ).set_extra(xpath="./tei:form/tei:orth", node_type="text")
    pos = models.CharField(
        blank=True,
        null=True,
        max_length=20,
        verbose_name="POS",
        choices=POS_CHOICES,
    ).set_extra(xpath="./tei:gramGrp/tei:pos", node_type="text")
    gram = models.CharField(
        blank=True,
        null=True,
        max_length=250,
        verbose_name="Grammatik",
        choices=POS_CHOICES,
    ).set_extra(xpath="./tei:gramGrp/tei:gram", node_type="text")

    class Meta:
        verbose_name = "Zusatzlemma"
        verbose_name_plural = "Zusatzlemmata"
        ordering = ["citation", "number"]

    def __str__(self):
        if self.form_orth:
            return f"{self.form_orth}"
        else:
            return f"{self.dboe_id}"

    def save(self, *args, **kwargs):
        if self.orig_xml is not None:
            try:
                doc = TeiReader(self.orig_xml)
            except AttributeError:
                doc = TeiReader(ET.tostring(self.orig_xml).decode("utf-8"))
            for field in self._meta.fields:
                if (
                    hasattr(field, "extra")
                    and "xpath" in field.extra
                    and isinstance(field, (models.CharField, models.TextField))
                    and not getattr(self, field.name)
                ):
                    xpath_expr = field.extra["xpath"]
                    try:
                        nodes = doc.any_xpath(xpath_expr)[0]
                    except IndexError:
                        continue
                    try:
                        value = extract_fulltext(nodes)
                    except AttributeError:
                        value = nodes
                    setattr(self, field.name, value)
        super().save(*args, **kwargs)


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
    orig_xml = XMLField(verbose_name="original tei-cit node")
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
    definition = models.TextField(
        blank=True,
        null=True,
        verbose_name="Bedeutung des Kontexts",
        help_text='Diese Information beschreibt die Bedeutung des in Spalte "Belegsatz 1", "Belegsatz 2" etc. angegebenen Belegsatze',  # noqa: E501
    ).set_extra(xpath="./tei:def", node_type="text")
    definition_lang = models.CharField(
        max_length=3,
        choices=LANG_CHOICES,
        blank=True,
        null=True,
        verbose_name="Sprache (Definition)",
    ).set_extra(xpath="./tei:def/@xml:lang", node_type="attribute")
    corresp = models.CharField(
        max_length=250,
        blank=True,
        null=True,
        verbose_name="Korrespondiert zu",
    ).set_extra(xpath="./@corresp", node_type="attribute")
    definition_corresp = models.CharField(
        max_length=250,
        blank=True,
        null=True,
        verbose_name="Definition korrespondiert zu Kontext",
    ).set_extra(xpath="./tei:def/@corresp", node_type="attribute")
    interpration = models.TextField(
        blank=True,
        null=True,
        verbose_name="interpretation",
        help_text="Summarizes a specific interpretative annotation which can be linked to a span of text",
    ).set_extra(xpath="./tei:interp", node_type="text")
    note_anmerkung_o = models.TextField(
        blank=True,
        null=True,
        verbose_name="Anmerkung: O",
        help_text="Whatever",
    ).set_extra(xpath="./tei:note[@type='anmerkung' and @resp='O']", node_type="text")
    note_anmerkung_b = models.TextField(
        blank=True,
        null=True,
        verbose_name="Anmerkung: B",
        help_text="Whatever",
    ).set_extra(xpath="./tei:note[@type='anmerkung' and @resp='B']", node_type="text")
    fragebogen_nummer = models.TextField(
        blank=True,
        null=True,
        verbose_name="Fragebogen Nummer",
        help_text="Whatever",
    ).set_extra(xpath="./tei:ref[@type='fragebogenNummer']", node_type="text")
    xr = models.CharField(
        max_length=300,
        blank=True,
        null=True,
        verbose_name="Cross-reference phrase",
        help_text="Contains a phrase, sentence, or icon referring the reader to some other location in this or another text",  # noqa: E501
    ).set_extra(xpath="./tei:xr[@type='verweise']", node_type="text")
    note_diverse = ArrayField(
        models.TextField(blank=True, null=True),
        blank=True,
        default=list,
        verbose_name="Anmerkung (diverse)",
        help_text="whatever",
    ).set_extra(xpath="./tei:note[@type='diverse']", node_type="list")

    class Meta:
        verbose_name = "Kontext"
        verbose_name_plural = "Kontexte"
        ordering = ["beleg", "number"]

    def save(self, add_zusatzlemma=False, *args, **kwargs):
        if self.orig_xml is not None:
            try:
                doc = TeiReader(self.orig_xml)
            except AttributeError:
                doc = TeiReader(ET.tostring(self.orig_xml).decode("utf-8"))
            for field in self._meta.fields:
                if (
                    hasattr(field, "extra")
                    and "xpath" in field.extra
                    and isinstance(field, (models.CharField, models.TextField))
                    and not getattr(self, field.name)
                ):
                    xpath_expr = field.extra["xpath"]
                    try:
                        nodes = doc.any_xpath(xpath_expr)[0]
                    except IndexError:
                        continue
                    try:
                        value = extract_fulltext(nodes)
                    except AttributeError:
                        value = nodes
                    setattr(self, field.name, value)
                if isinstance(field, ArrayField) and not getattr(self, field.name):
                    xpath_expr = field.extra["xpath"]
                    try:
                        nodes = doc.any_xpath(xpath_expr)
                    except IndexError:
                        continue
                    values = []
                    for node in nodes:
                        try:
                            value = extract_fulltext(node)
                        except AttributeError:
                            value = node
                        if isinstance(value, str):
                            value = value.strip()
                        values.append(value)
                    setattr(self, field.name, values)
        if self.orig_xml is not None and add_zusatzlemma:
            items = doc.any_xpath("./tei:re")
            for number, item in enumerate(items, start=1):
                xml_id = get_xmlid(item)
                orig_xml = ET.tostring(item, encoding="unicode")
                try:
                    item = ZusatzLemma.objects.get(dboe_id=xml_id)
                except ZusatzLemma.DoesNotExist:
                    item = ZusatzLemma(
                        dboe_id=xml_id, citation=self, number=number, orig_xml=orig_xml
                    )
                try:
                    item.save()
                except Exception as e:
                    print(f"Error saving ZusatzLemma {xml_id}: {e}")
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
        help_text="e.g. tu-10130.56",
    )
    beleg = models.ForeignKey(
        "Beleg",
        verbose_name="Beleg",
        on_delete=models.CASCADE,
        related_name="lautungen",
    )
    number = models.PositiveIntegerField(default=1, verbose_name="Order number")
    orig_xml = XMLField(
        verbose_name="XML Node", help_text="tei:form[@type='lautung'] node"
    )
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

    def save(self, *args, **kwargs):
        if self.orig_xml is not None:
            try:
                doc = TeiReader(self.orig_xml)
            except AttributeError:
                doc = TeiReader(ET.tostring(self.orig_xml).decode("utf-8"))
            for field in self._meta.fields:
                if (
                    hasattr(field, "extra")
                    and "xpath" in field.extra
                    and isinstance(field, (models.CharField, models.TextField))
                    and not getattr(self, field.name)
                ):
                    xpath_expr = field.extra["xpath"]
                    try:
                        nodes = doc.any_xpath(xpath_expr)[0]
                    except IndexError:
                        continue
                    try:
                        value = extract_fulltext(nodes)
                    except AttributeError:
                        value = nodes
                    setattr(self, field.name, value)
        super().save(*args, **kwargs)


class LehnWort(models.Model):
    """
    Django model representing a tei:form[@type="lautung"] node.
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
        related_name="lehnwoerter",
    )
    number = models.PositiveIntegerField(default=1, verbose_name="Order number")
    orig_xml = XMLField(
        verbose_name="XML Node", help_text="tei:form[@type='lehnwort'] node"
    )
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

    def save(self, *args, **kwargs):
        if self.orig_xml is not None:
            try:
                doc = TeiReader(self.orig_xml)
            except AttributeError:
                doc = TeiReader(ET.tostring(self.orig_xml).decode("utf-8"))
            for field in self._meta.fields:
                if (
                    hasattr(field, "extra")
                    and "xpath" in field.extra
                    and isinstance(field, (models.CharField, models.TextField))
                    and not getattr(self, field.name)
                ):
                    xpath_expr = field.extra["xpath"]
                    try:
                        nodes = doc.any_xpath(xpath_expr)[0]
                    except IndexError:
                        continue
                    try:
                        value = extract_fulltext(nodes)
                    except AttributeError:
                        value = nodes
                    setattr(self, field.name, value)
        super().save(*args, **kwargs)


class AnmerkungLautung(models.Model):
    """Django model representing a tei:note related to a Lautung object"""

    dboe_id = models.CharField(
        primary_key=True,
        max_length=250,
        verbose_name="DBÖ ID",
        help_text="Kombination of the Beleg-ID and the @n",
    )
    beleg = models.ForeignKey(
        "Beleg",
        verbose_name="Beleg",
        on_delete=models.CASCADE,
        related_name="note_lautung",
    )
    number = models.PositiveIntegerField(default=1, verbose_name="Order number")
    resp = models.CharField(
        choices=RESP_OPTIONS,
        max_length=1,
        default="O",
        verbose_name="Responsible (O/B)",
        help_text="whatever",
    )
    corresp_to = models.CharField(
        blank=True, null=True, max_length=20, verbose_name="Korrespondiert zu"
    )
    content = models.TextField(blank=True, null=True, verbose_name="Anmerkung")
    p_ref = ArrayField(
        models.TextField(blank=True, null=True),
        blank=True,
        default=list,
        verbose_name="Pronunciation reference",
        help_text="Iindicates a reference to the pronunciation(s) of the headword",
    )

    class Meta:
        verbose_name = "Anmerkung (Lautung)"
        verbose_name_plural = "Anmerkungen (Lautung)"
        ordering = ["beleg", "number"]

    def __str__(self):
        return f"{self.dboe_id}"


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
    orig_xml = XMLField(verbose_name="XML Node", help_text="tei:sense node")
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
    note_anmerkung_o = models.TextField(
        blank=True,
        null=True,
        verbose_name="Anmerkung: O",
        help_text="Whatever",
    ).set_extra(xpath="./tei:note[@type='anmerkung' and @resp='O']", node_type="text")
    note_anmerkung_b = models.TextField(
        blank=True,
        null=True,
        verbose_name="Anmerkung: B",
        help_text="Whatever",
    ).set_extra(xpath="./tei:note[@type='anmerkung' and @resp='B']", node_type="text")

    class Meta:
        verbose_name = "Bedeutung"
        verbose_name_plural = "Bedeutungen"
        ordering = ["beleg", "number"]

    def __str__(self):
        return f"{self.definition[:25]} ... ({self.beleg})"

    def save(self, *args, **kwargs):
        if self.orig_xml is not None:
            try:
                doc = TeiReader(self.orig_xml)
            except AttributeError:
                doc = TeiReader(ET.tostring(self.orig_xml).decode("utf-8"))
            for field in self._meta.fields:
                if (
                    hasattr(field, "extra")
                    and "xpath" in field.extra
                    and isinstance(field, (models.CharField, models.TextField))
                    and not getattr(self, field.name)
                ):
                    xpath_expr = field.extra["xpath"]
                    try:
                        nodes = doc.any_xpath(xpath_expr)[0]
                    except IndexError:
                        continue
                    try:
                        value = extract_fulltext(nodes)
                    except AttributeError:
                        value = nodes
                    setattr(self, field.name, value)
        super().save(*args, **kwargs)


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
    pos = models.CharField(
        blank=True,
        null=True,
        max_length=20,
        verbose_name="Part of Speech",
        help_text="Diese Angabe benennt die Wortart des jeweiligen Belegs.",
        choices=POS_CHOICES,
    ).set_extra(xpath="./tei:gramGrp/tei:pos", node_type="text")
    ref_type_dbo = models.CharField(
        blank=True,
        null=True,
        max_length=250,
        verbose_name="Verweis (ref/@type='dbo')",
    ).set_extra(xpath=".//tei:ref[@type='dbo']", node_type="text")
    ref_type_sni = models.CharField(
        blank=True,
        null=True,
        max_length=250,
        verbose_name="Verweis (ref/@type='sni')",
    ).set_extra(xpath="./tei:ref[@type='sni']", node_type="text")
    xr_type_verweise_o = models.CharField(
        blank=True,
        null=True,
        max_length=250,
        verbose_name="Verweis (xr/@type='verweise' and @resp='O')",
    ).set_extra(xpath="./tei:xr[@type='verweise' and @resp='O']", node_type="text")
    xr_type_verweise_b = models.CharField(
        blank=True,
        null=True,
        max_length=250,
        verbose_name="Verweis (xr/@type='verweise' and @resp='B')",
    ).set_extra(xpath="./tei:xr[@type='verweise' and @resp='B']", node_type="text")
    fragebogen_nummer = models.TextField(
        blank=True,
        null=True,
        verbose_name="Fragebogen Nummer",
        help_text="Whatever",
    ).set_extra(xpath="./tei:ref[@type='fragebogenNummer']", node_type="text")
    etym = ArrayField(
        models.TextField(blank=True, null=True),
        blank=True,
        default=list,
        verbose_name="Etymologie",
        help_text="whatever",
    ).set_extra(xpath="./tei:etym", node_type="list")
    note_notabene = ArrayField(
        models.TextField(blank=True, null=True),
        blank=True,
        default=list,
        verbose_name="Notabene",
        help_text="whatever",
    ).set_extra(xpath="./tei:note[@type='notabene']", node_type="list")
    note_diverse = ArrayField(
        models.TextField(blank=True, null=True),
        blank=True,
        default=list,
        verbose_name="Anmerkung (diverse)",
        help_text="whatever",
    ).set_extra(xpath="./tei:note[@type='diverse']", node_type="list")
    facs = models.ManyToManyField(
        "Facsimile",
        blank=True,
        verbose_name="Faksimiles",
        help_text="whatever",
        related_name="belege",
        through="BelegFacs",
    )
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

    class Meta:
        verbose_name = "Beleg"
        verbose_name_plural = "Belege"
        ordering = ["dboe_id"]

    def __str__(self):
        if self.hauptlemma:
            return f"{self.dboe_id} ({self.hauptlemma})"
        return f"{self.dboe_id}"

    def save(
        self,
        add_citations=False,
        add_lautungen=False,
        add_sense=False,
        add_anmkerung_laut=False,
        add_lehnwort=False,
        *args,
        **kwargs,
    ):
        if self.orig_xml is not None:
            self.import_issue = False
            try:
                doc = TeiReader(self.orig_xml)
            except AttributeError:
                doc = TeiReader(ET.tostring(self.orig_xml).decode("utf-8"))
            for field in self._meta.fields:
                if (
                    hasattr(field, "extra")
                    and "xpath" in field.extra
                    and isinstance(field, (models.CharField, models.TextField))
                    and not getattr(self, field.name)
                ):
                    if self.orig_xml is not None:
                        xpath_expr = field.extra["xpath"]
                        try:
                            nodes = doc.any_xpath(xpath_expr)[0]
                        except IndexError:
                            continue
                        try:
                            value = extract_fulltext(nodes)
                        except AttributeError:
                            value = nodes
                        if isinstance(field, models.CharField):
                            if field.max_length and len(value) > field.max_length:
                                value = value[: field.max_length]
                                self.import_issue = True
                        if isinstance(field, (models.CharField, models.TextField)):
                            value = value.strip()
                        setattr(self, field.name, value)
                if isinstance(field, ArrayField) and not getattr(self, field.name):
                    xpath_expr = field.extra["xpath"]
                    try:
                        nodes = doc.any_xpath(xpath_expr)
                    except IndexError:
                        continue
                    values = []
                    for node in nodes:
                        try:
                            value = extract_fulltext(node)
                        except AttributeError:
                            value = node
                        if isinstance(value, str):
                            value = value.strip()
                        values.append(value)
                    setattr(self, field.name, values)
        if self.orig_xml is not None and add_anmkerung_laut:
            items = doc.any_xpath(
                "./tei:note[@type='anmerkung' and @resp and @corresp]"
            )
            for i, item in enumerate(items, start=1):
                try:
                    number = item.attrib["number"]
                except KeyError:
                    number = i
                dboe_id = f"{self.dboe_id}_{number:0>2}"
                item_object, _ = AnmerkungLautung.objects.get_or_create(
                    dboe_id=dboe_id, beleg=self
                )
                item_object.number = number
                item_object.corresp_to = item.attrib["corresp"]
                item_object.resp = item.attrib["resp"]
                item_object.content = extract_fulltext(item)
                p_refs = []
                for x in item.xpath(".//tei:pRef", namespaces=NSMAP):
                    p_refs.append(extract_fulltext(x))
                item_object.p_ref = p_refs
                try:
                    item_object.save()
                except Exception as e:
                    print(f"Error saving AnmerkungLautung {dboe_id}: {e}")
        if self.orig_xml is not None and add_citations:
            items = doc.any_xpath("./tei:cit")
            for n, item in enumerate(items, start=1):
                xml_id = get_xmlid(item)
                try:
                    number = item.attrib["n"]
                except KeyError:
                    number = n
                orig_xml = ET.tostring(item, encoding="unicode")
                try:
                    item = Citation.objects.get(dboe_id=xml_id)
                except Citation.DoesNotExist:
                    item = Citation(
                        dboe_id=xml_id, beleg=self, number=number, orig_xml=orig_xml
                    )
                try:
                    item.save()
                except Exception as e:
                    print(f"Error saving citation {xml_id}: {e}")
        if self.orig_xml is not None and add_lautungen:
            items = doc.any_xpath("./tei:form[@type='lautung']")
            for item in items:
                xml_id = get_xmlid(item)
                try:
                    number = item.attrib["n"]
                except KeyError:
                    number = 1
                orig_xml = ET.tostring(item, encoding="unicode")
                try:
                    item = Lautung.objects.get(dboe_id=xml_id)
                except Lautung.DoesNotExist:
                    item = Lautung(
                        dboe_id=xml_id, beleg=self, number=number, orig_xml=orig_xml
                    )
                try:
                    item.save()
                except Exception as e:
                    print(f"Error saving lautung {xml_id}: {e}")
        if self.orig_xml is not None and add_lehnwort:
            items = doc.any_xpath("./tei:form[@type='lehnwort']")
            for item in items:
                xml_id = get_xmlid(item)
                try:
                    number = item.attrib["n"]
                except KeyError:
                    number = 1
                orig_xml = ET.tostring(item, encoding="unicode")
                try:
                    item = LehnWort.objects.get(dboe_id=xml_id)
                except LehnWort.DoesNotExist:
                    item = LehnWort(
                        dboe_id=xml_id, beleg=self, number=number, orig_xml=orig_xml
                    )
                try:
                    item.save()
                except Exception as e:
                    print(f"Error saving LehnWort {xml_id}: {e}")
        if self.orig_xml is not None and add_sense:
            items = doc.any_xpath("./tei:sense")
            for i, item in enumerate(items, start=1):
                xml_id = get_xmlid(item)
                number = i
                orig_xml = ET.tostring(item, encoding="unicode")
                try:
                    item = Sense.objects.get(dboe_id=xml_id)
                except Sense.DoesNotExist:
                    item = Sense(
                        dboe_id=xml_id, beleg=self, number=number, orig_xml=orig_xml
                    )
                try:
                    item.save()
                except Exception as e:
                    print(f"Error saving sense {xml_id}: {e}")
        if OS_CONNECTION:
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
                "nl": self.nebenlemma,
                "qu": self.quelle,
                "bibl": self.bibl,
                "pos": self.pos,
                "archivzeile": self.archivzeile,
            }

        ret = dict(base)  # copy so we don't mutate caller provided dict

        # Collect simple references
        ret["tustep"] = self.xeno_data
        ret["facs"] = self.facs.values_list("file_name", flat=True)
        verweise = []
        for x in [
            "ref_type_dbo",
            "ref_type_sni",
            "xr_type_verweise_o",
            "xr_type_verweise_b",
        ]:
            value = getattr(self, x, None)
            if value:
                verweise.append(value)

        try:
            cit_fragebogen_nr = " ".join(
                self.citations.all().values_list("fragebogen_nummer", flat=True)
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
        ret["etym"] = self.etym
        ret["a"] = self.archivzeile

        siglen = set()
        bundeslaender = set()
        gregion = set()
        kregion = set()
        orte = set()
        orig_orte = list()
        for x in self.belegsigle_set.select_related("sigle"):
            siglen.add(x.sigle.sigle)
            orte.add(x.sigle.name)
            for y in x.sigle.orig_names:
                orig_orte.append(y)
            try:
                bundeslaender.add(f"{x.sigle.bl}")
            except AttributeError:
                pass
            try:
                gregion.add(f"{x.sigle.gr}")
            except AttributeError:
                pass
            try:
                kregion.add(f"{x.sigle.kr}")
            except AttributeError:
                pass
        ret["siglen"] = list(siglen)
        ret["bundeslaender"] = list(bundeslaender)
        ret["gregion"] = list(gregion)
        ret["kregion"] = list(kregion)
        ret["orte"] = list(orte)
        ret["orig_orte"] = orig_orte

        # DV/LW*
        ret["dv_lw_star"] = []
        for x in self.note_diverse:
            ret["dv_lw_star"].append(x)

        # Lautungen
        for x in self.lautungen.all():
            gram_key = f"gram_lt{x.number}"
            ret[gram_key] = [x.pron_gram]
            teut_key = f"lt{x.number}_teuthonista"
            ret[teut_key] = [x.pron]

        # Lehnwörter
        for x in self.lehnwoerter.all():
            number = x.number
            ret[f"lw{number}"] = x.pron

        # Notes Lautung
        ret["anm_lt_star"] = self.note_lautung.all().values_list("content", flat=True)
        try:
            ret["kl_kt1"] = self.citations.filter(number=1).first().interpration
        except AttributeError:
            pass

        ret["anm_kt_star"] = []
        ret["bd_kt_star"] = []
        ret["wbd_kt_star"] = []
        ret["vrw_kt_star"] = []
        ret["dv_kt_star"] = []

        for x in self.citations.all():
            if x.corresp and "this:LT" in x.corresp:
                cur_lt = x.corresp.split(":")[-1]
                key = f"kt_{cur_lt.lower()}"
                value = x.quote_text
                ret[key] = value
            if x.definition_corresp is None and x.definition:
                ret["bd_kt_star"].append(f"{x.definition} ›KT {x.number}")
            elif x.definition:
                ret["wbd_kt_star"].append(
                    f"{x.definition} ›WBD/KT{x.number}/KT{x.number}"
                )
            ret[f"kt{x.number}"] = [x.quote_text]
            for y in x.zusatz_lemma.all():
                ret[f"zl{y.number}_kt{x.number}"] = [
                    f"{y.form_orth}||{y.pos}||{getattr(y, 'gram', None) or ''}"
                ]
            for y in x.note_diverse:
                ret["dv_kt_star"].append(f"{y} ›KT {x.number}")
            if x.xr:
                ret["vrw_kt_star"].append(f"O: {x.xr} ›KT{x.number}")
            if x.note_anmerkung_o:
                ret["anm_kt_star"].append(f"O: {x.note_anmerkung_o} ›KT{x.number}")
            if x.note_anmerkung_b:
                ret["anm_kt_star"].append(f"B: {x.note_anmerkung_b} ›KT{x.number}")

        ret["bd_lw_star"] = self.bedeutungen.filter(
            corresp_to__contains="LW"
        ).values_list("definition", flat=True)
        for i in ["1", "2"]:
            ret[f"bd_kt_lt{i}"] = self.citations.filter(
                corresp=f"this:LT{i}",
                definition_corresp=None,
                definition__isnull=False,
            ).values_list("definition", flat=True)
            ret[f"kt_lt{i}"] = self.citations.filter(
                corresp=f"this:LT{i}", quote_text__isnull=False
            ).values_list("quote_text", flat=True)
            kontext = self.citations.filter(corresp=f"this:LT{i}")
            zl = ZusatzLemma.objects.filter(citation__in=kontext)
            ret[f"zl1_kt_lt{i}"] = ""
            ret[f"zl2_kt_lt{i}"] = ""
            for n, y in enumerate(zl, start=1):
                ret[f"zl{n}_kt_lt{i}"] = (
                    f"{y.form_orth}||{getattr(y, 'pos', None) or ''}||{getattr(y, 'gram', None) or ''}"
                )

        ret["anm_lw_star"] = []
        for x in self.note_lautung.filter(corresp_to__icontains="this:LW1"):
            ret["anm_lw_star"].append(
                f"{x.resp}: {x.content} ›{x.corresp_to.replace('this:', '')}"
            )

        ret["bd_lt_star"] = []
        for x in self.bedeutungen.filter(corresp_to__contains="LT"):
            if x.note_anmerkung_o:
                ret["bd_lt_star"].append(
                    f"{x.definition}ANMO: {x.note_anmerkung_o} ›LT{x.number}"
                )
            else:
                ret["bd_lt_star"].append(f"{x.definition} ›LT{x.number}")

        for i, x in enumerate(self.zitierweise, start=1):
            ret[f"zw{i}"] = [x]
        return ret

    def sanitize_representation(self):
        raw = self.build_representation()
        processed = transform_record(raw)
        return processed


class BelegFacs(models.Model):
    beleg = models.ForeignKey(Beleg, on_delete=models.CASCADE)
    facsimile = models.ForeignKey(Facsimile, on_delete=models.CASCADE)
    resp = models.CharField(
        default="system",
        max_length=250,
        verbose_name="Responsible for linking",
        help_text="Name of user or script resposnible for linking Beleg to Facsimile",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created at",
        help_text="Timestamp when the link was created",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated at",
        help_text="Timestamp when the link was last updated",
    )

    class Meta:
        verbose_name = "Beleg-Facsimile Link"
        verbose_name_plural = "Beleg-Facsimile Links"
        ordering = ["beleg", "facsimile"]

    def __str__(self):
        return f"Link: {self.beleg} <-> {self.facsimile}"
