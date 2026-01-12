from django.urls import path

from stats import views

app_name = "belege"

urlpatterns = [
    path("belege-by-collection/", views.beleg_by_collection),
    path("collection-by-beleg/", views.collection_by_beleg_count),
    path("tags-by-beleg/", views.tag_by_beleg),
]
