from django.urls import path

from stats import views

app_name = "belege"

urlpatterns = [
    path("belege-by-anmerkung-lautung/", views.beleg_by_note_lautung_count),
    path("belege-by-bedeutung/", views.beleg_by_sense_count),
    path("belege-by-collection/", views.beleg_by_collection_count),
    path("belege-by-context/", views.beleg_by_context_count),
    path("belege-by-facs/", views.beleg_by_facs_count),
    path("belege-by-lautung/", views.beleg_by_lautung_count),
    path("belege-by-lehnwort/", views.beleg_by_lehnwort_count),
    path("collection-by-beleg/", views.collection_by_beleg_count),
    path("tags-by-beleg/", views.tag_by_beleg_count),
]
