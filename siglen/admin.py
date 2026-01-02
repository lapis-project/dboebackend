from django.contrib import admin

from siglen.models import Sigle


@admin.register(Sigle)
class SigleAdmin(admin.ModelAdmin):
    list_display = ["sigle", "name", "bl", "gr", "kr", "geonames", "kind"]
    search_fields = ["name", "sigle"]
    list_filter = ["kind"]
    autocomplete_fields = ["bl", "gr", "kr"]
    ordering = ["sigle"]
    list_per_page = 50
