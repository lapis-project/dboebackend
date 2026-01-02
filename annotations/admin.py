from django.contrib import admin

from .models import Annotation, Category, Collection, Es_document, Lemma, Tag

admin.site.register(Annotation)
admin.site.register(Category)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "color"]
    search_fields = ["name"]
    ordering = ["name"]


@admin.register(Lemma)
class LemmaAdmin(admin.ModelAdmin):
    list_display = [
        "norm",
    ]
    search_fields = ["norm"]
    ordering = ["-id"]
    autocomplete_fields = ["simplex"]


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = [
        "title",
    ]
    search_fields = ["title"]
    ordering = ["-modified"]
    autocomplete_fields = ["es_document", "lemma_id"]


@admin.register(Es_document)
class Es_documentAdmin(admin.ModelAdmin):
    list_display = [
        "es_id",
    ]
    search_fields = ["es_id"]
    ordering = ["-id"]
