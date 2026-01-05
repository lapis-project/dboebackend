from django.db import models
from django_jsonform.models.fields import ArrayField

sigle_kinds = (
    ("bl", "Bundesland"),
    ("gr", "Großregion"),
    ("kr", "Kleinregion"),
    ("ort", "Ort"),
)


class Sigle(models.Model):
    sigle = models.CharField(
        primary_key=True, max_length=50, verbose_name="Sigle", help_text="Sigle"
    )
    name = models.CharField(verbose_name="Name", help_text="Name")
    orig_names = ArrayField(
        models.CharField(max_length=250),
        default=list,
        blank=True,
        verbose_name="Original Ortsnamen",
    )
    kind = models.CharField(choices=sigle_kinds, verbose_name="Art der Sigle")
    coordinates = models.JSONField(blank=True, null=True, verbose_name="Koordinaten")
    geonames = models.URLField(
        blank=True, null=True, max_length=250, verbose_name="Geonames URL"
    )
    bl = models.ForeignKey(
        "self", blank=True, null=True, on_delete=models.CASCADE, related_name="has_bl"
    )
    gr = models.ForeignKey(
        "self", blank=True, null=True, on_delete=models.CASCADE, related_name="has_gr"
    )
    kr = models.ForeignKey(
        "self", blank=True, null=True, on_delete=models.CASCADE, related_name="has_kr"
    )

    class Meta:
        verbose_name = "Sigle"
        verbose_name_plural = "Siglen"
        ordering = ["sigle"]

    def __str__(self):
        return f"{self.sigle} {self.name}"

    def save(self, *args, **kwargs):
        self.orig_names = list(set(self.orig_names))
        super().save(*args, **kwargs)


class BelegSigle(models.Model):
    beleg = models.ForeignKey(
        "belege.Beleg", on_delete=models.CASCADE, verbose_name="Beleg"
    )
    sigle = models.ForeignKey("Sigle", on_delete=models.CASCADE, verbose_name="Sigle")
    corresp = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="@corrsp"
    )
    resp = models.CharField(max_length=50, blank=True, null=True, verbose_name="@resp")

    class Meta:
        verbose_name = "Beleg-Sigle"
        verbose_name_plural = "Belege-Siglen"
        ordering = ["sigle"]

    def __str__(self):
        return f"{self.sigle} ({self.beleg}) {self.corresp}"
