from django.contrib import admin
from django.db import models

from belege.models import (
    AnmerkungLautung,
    Annotation,
    Beleg,
    BelegFacs,
    BundesLand,
    Citation,
    Facsimile,
    GeoRelationBundesland,
    GeoRelationGregion,
    GeoRelationKregion,
    GeoRelationOrt,
    GRegion,
    KRegion,
    Lautung,
    LehnWort,
    Ort,
    Sense,
    ZusatzLemma,
)


@admin.register(Annotation)
class AnnotationAdmin(admin.ModelAdmin):
    list_display = ["kontext", "tool", "created_at", "updated_at"]
    search_fields = ["kontext__dboe_id", "tool"]
    autocomplete_fields = ["kontext"]
    ordering = ["kontext", "created_at"]
    list_per_page = 20


@admin.register(Facsimile)
class FacsimileAdmin(admin.ModelAdmin):
    list_display = ["file_name"]
    search_fields = ["file_name"]
    ordering = ["file_name"]
    list_per_page = 20


@admin.register(BelegFacs)
class BelegFacsAdmin(admin.ModelAdmin):
    list_display = ["beleg", "facsimile", "created_at", "updated_at"]
    search_fields = ["beleg__dboe_id", "facsimile__identifier"]
    autocomplete_fields = ["beleg", "facsimile"]
    ordering = ["beleg", "facsimile"]
    list_per_page = 20


@admin.register(GeoRelationBundesland)
class GeoRelationBundeslandAdmin(admin.ModelAdmin):
    list_display = ["beleg", "ort", "corresp"]
    search_fields = ["beleg__dboe_id", "ort__name"]
    autocomplete_fields = ["beleg", "ort"]
    ordering = ["beleg", "ort"]
    list_per_page = 20


@admin.register(GeoRelationGregion)
class GeoRelationGregionAdmin(admin.ModelAdmin):
    list_display = ["beleg", "ort", "corresp"]
    search_fields = ["beleg__dboe_id", "ort__name"]
    autocomplete_fields = ["beleg", "ort"]
    ordering = ["beleg", "ort"]
    list_per_page = 20


@admin.register(GeoRelationKregion)
class GeoRelationKregionAdmin(admin.ModelAdmin):
    list_display = ["beleg", "ort", "corresp"]
    search_fields = ["beleg__dboe_id", "ort__name"]
    autocomplete_fields = ["beleg", "ort"]
    ordering = ["beleg", "ort"]
    list_per_page = 20


@admin.register(GeoRelationOrt)
class GeoRelationOrtAdmin(admin.ModelAdmin):
    list_display = ["beleg", "ort", "corresp"]
    search_fields = ["beleg__dboe_id", "ort__name"]
    autocomplete_fields = ["beleg", "ort"]
    ordering = ["beleg", "ort"]
    list_per_page = 20


@admin.register(LehnWort)
class LehnWortAdmin(admin.ModelAdmin):
    list_display = [
        field.name
        for field in LehnWort._meta.fields
        if isinstance(
            field,
            (
                models.CharField,
                models.TextField,
                models.ForeignKey,
                models.PositiveIntegerField,
            ),
        )
    ]
    search_fields = [
        field.name
        for field in ZusatzLemma._meta.fields
        if isinstance(field, (models.CharField, models.TextField))
    ]
    autocomplete_fields = ["beleg"]
    ordering = ["beleg", "number"]
    list_per_page = 20


@admin.register(AnmerkungLautung)
class AnmerkungLautungAdmin(admin.ModelAdmin):
    list_display = [
        field.name
        for field in AnmerkungLautung._meta.fields
        if isinstance(
            field,
            (
                models.CharField,
                models.TextField,
                models.ForeignKey,
                models.PositiveIntegerField,
            ),
        )
    ]
    # Include foreign key fields and their related object's string representation in search_fields
    search_fields = [
        field.name
        for field in AnmerkungLautung._meta.fields
        if isinstance(field, (models.CharField, models.TextField))
    ] + ["beleg__dboe_id"]
    autocomplete_fields = ["beleg"]
    ordering = ["beleg", "number"]
    list_per_page = 20


@admin.register(ZusatzLemma)
class ZusatzLemmaAdmin(admin.ModelAdmin):
    list_display = [
        field.name
        for field in ZusatzLemma._meta.fields
        if isinstance(
            field,
            (
                models.CharField,
                models.TextField,
                models.ForeignKey,
                models.PositiveIntegerField,
            ),
        )
    ]
    search_fields = [
        field.name
        for field in ZusatzLemma._meta.fields
        if isinstance(field, (models.CharField, models.TextField))
    ]
    autocomplete_fields = ["citation"]
    ordering = ["citation", "number"]
    list_per_page = 20


@admin.register(Sense)
class SenseAdmin(admin.ModelAdmin):
    list_display = [
        field.name
        for field in Sense._meta.fields
        if isinstance(
            field,
            (
                models.CharField,
                models.TextField,
                models.ForeignKey,
                models.PositiveIntegerField,
            ),
        )
    ]
    search_fields = [
        field.name
        for field in Sense._meta.fields
        if isinstance(field, (models.CharField, models.TextField))
    ]
    autocomplete_fields = ["beleg"]
    ordering = ["beleg", "number"]
    list_per_page = 20


@admin.register(Lautung)
class LautungAdmin(admin.ModelAdmin):
    list_display = [
        field.name
        for field in Lautung._meta.fields
        if isinstance(
            field,
            (
                models.CharField,
                models.TextField,
                models.ForeignKey,
                models.PositiveIntegerField,
            ),
        )
    ]
    search_fields = [
        field.name
        for field in Lautung._meta.fields
        if isinstance(field, (models.CharField, models.TextField))
    ]
    autocomplete_fields = ["beleg"]
    ordering = ["beleg", "number"]
    list_per_page = 20


@admin.register(Beleg)
class BelegAdmin(admin.ModelAdmin):
    list_display = [
        field.name
        for field in Beleg._meta.fields
        if isinstance(
            field,
            (
                models.CharField,
                models.TextField,
                models.ForeignKey,
                models.PositiveIntegerField,
            ),
        )
    ]
    search_fields = [
        field.name
        for field in Beleg._meta.fields
        if isinstance(field, (models.CharField, models.TextField))
    ]
    list_filter = ["import_issue", "pos"]
    ordering = ["dboe_id"]
    autocomplete_fields = ["ort", "tag"]
    list_per_page = 20


@admin.register(Citation)
class CitationAdmin(admin.ModelAdmin):
    list_display = [
        field.name
        for field in Citation._meta.fields
        if isinstance(
            field, (models.CharField, models.TextField, models.PositiveIntegerField)
        )
    ]
    search_fields = [
        field.name
        for field in Citation._meta.fields
        if isinstance(field, (models.CharField, models.TextField))
    ] + ["beleg__dboe_id"]
    ordering = ["beleg", "number"]
    autocomplete_fields = ["beleg"]
    list_per_page = 20


@admin.register(BundesLand)
class BundesLandAdmin(admin.ModelAdmin):
    list_display = ["sigle", "abbr", "name", "geonames"]
    search_fields = ["sigle", "abbr", "name"]
    ordering = ["name"]


@admin.register(GRegion)
class GRegionAdmin(admin.ModelAdmin):
    list_display = ["sigle", "abbr", "name", "bundesland"]
    search_fields = ["sigle", "abbr", "name"]
    ordering = ["name"]
    list_filter = ["bundesland"]


@admin.register(KRegion)
class KRegionAdmin(admin.ModelAdmin):
    list_display = ["sigle", "abbr", "name", "bundesland", "gregion", "geonames"]
    search_fields = ["sigle", "abbr", "name"]
    autocomplete_fields = ["bundesland", "gregion"]
    ordering = ["name"]
    list_filter = ["bundesland", "gregion"]


@admin.register(Ort)
class OrtAdmin(admin.ModelAdmin):
    list_display = ["sigle", "name", "bundesland", "gregion", "kregion", "geonames"]
    search_fields = ["sigle", "name"]
    autocomplete_fields = ["bundesland", "gregion", "kregion"]
    ordering = ["name"]
