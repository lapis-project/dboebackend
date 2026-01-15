from django.db.models import Count, F
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response

from annotations.models import Collection, Tag
from belege.models import Beleg


@extend_schema(responses=dict)
@api_view(["get"])
def beleg_by_facs_count(request):
    payload = list(
        Beleg.objects.annotate(item_count=Count("facs"))
        .filter(item_count__gt=0)
        .order_by("-item_count")[:25]
        .values(id=F("dboe_id"), value=F("hauptlemma"), item_count=F("item_count"))
    )
    return Response({"title": "Belege nach Faksimiles)", "payload": payload})


@extend_schema(responses=dict)
@api_view(["get"])
def beleg_by_note_lautung_count(request):
    payload = list(
        Beleg.objects.annotate(item_count=Count("note_lautung"))
        .filter(item_count__gt=0)
        .order_by("-item_count")[:25]
        .values(id=F("dboe_id"), value=F("hauptlemma"), item_count=F("item_count"))
    )
    return Response({"title": "Belege nach Anmerkungen(Lautung)", "payload": payload})


@extend_schema(responses=dict)
@api_view(["get"])
def beleg_by_sense_count(request):
    payload = list(
        Beleg.objects.annotate(item_count=Count("bedeutungen"))
        .filter(item_count__gt=0)
        .order_by("-item_count")[:25]
        .values(id=F("dboe_id"), value=F("hauptlemma"), item_count=F("item_count"))
    )
    return Response({"title": "Belege nach Bedeutungen", "payload": payload})


@extend_schema(responses=dict)
@api_view(["get"])
def beleg_by_lehnwort_count(request):
    payload = list(
        Beleg.objects.annotate(item_count=Count("lehnwoerter"))
        .filter(item_count__gt=0)
        .order_by("-item_count")[:25]
        .values(id=F("dboe_id"), value=F("hauptlemma"), item_count=F("item_count"))
    )
    return Response({"title": "Belege nach Lehnwörtern", "payload": payload})


@extend_schema(responses=dict)
@api_view(["get"])
def beleg_by_lautung_count(request):
    payload = list(
        Beleg.objects.annotate(item_count=Count("lautungen"))
        .filter(item_count__gt=0)
        .order_by("-item_count")[:25]
        .values(id=F("dboe_id"), value=F("hauptlemma"), item_count=F("item_count"))
    )
    return Response({"title": "Belege nach Lautungen", "payload": payload})


@extend_schema(responses=dict)
@api_view(["get"])
def beleg_by_context_count(request):
    payload = list(
        Beleg.objects.annotate(item_count=Count("citations"))
        .filter(item_count__gt=0)
        .order_by("-item_count")[:25]
        .values(id=F("dboe_id"), value=F("hauptlemma"), item_count=F("item_count"))
    )
    return Response({"title": "Belege nach Kontexten", "payload": payload})


@extend_schema(responses=dict)
@api_view(["get"])
def collection_by_beleg_count(request):
    payload = list(
        Collection.objects.annotate(item_count=Count("beleg"))
        .filter(item_count__gt=0)
        .order_by("-item_count")[:25]
        .values("id", value=F("title"), item_count=F("item_count"))
    )
    return Response({"title": "Collection nach Belegen", "payload": payload})


@extend_schema(responses=dict)
@api_view(["get"])
def beleg_by_collection_count(request):
    payload = list(
        Beleg.objects.annotate(item_count=Count("collection"))
        .filter(item_count__gt=0)
        .order_by("-item_count")[:25]
        .values(id=F("dboe_id"), value=F("hauptlemma"), item_count=F("item_count"))
    )
    return Response({"title": "Belege nach Collections", "payload": payload})


@extend_schema(responses=dict)
@api_view(["get"])
def tag_by_beleg_count(request) -> dict:
    payload = list(
        Tag.objects.annotate(item_count=Count("belege"))
        .filter(item_count__gt=0)
        .order_by("-item_count")[:25]
        .values("id", value=F("name"), item_count=F("item_count"))
    )
    return Response({"title": "Tags nach Belegen", "payload": payload})
