from django.contrib import admin

from siglen.models import BelegSigle, Sigle


@admin.register(Sigle)
class SigleAdmin(admin.ModelAdmin):
    list_display = ["sigle", "name", "orig_names", "bl", "gr", "kr", "geonames", "kind"]
    search_fields = ["name", "sigle"]
    list_filter = ["kind"]
    autocomplete_fields = ["bl", "gr", "kr"]
    ordering = ["sigle"]
    list_per_page = 50


@admin.register(BelegSigle)
class BelegSigleAdmin(admin.ModelAdmin):
    list_display = ["beleg", "sigle", "corresp", "resp"]
    search_fields = ["beleg__dboe_id", "sigle__name", "sigle__sigle"]
    autocomplete_fields = ["beleg", "sigle"]
    ordering = ["sigle"]
    list_per_page = 50
