from django.contrib import admin

from .models import Annotation, Category, Collection, Es_document, Tag

admin.site.register(Collection)
admin.site.register(Annotation)
admin.site.register(Category)
admin.site.register(Es_document)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "color"]
    search_fields = ["name"]
    ordering = ["name"]
