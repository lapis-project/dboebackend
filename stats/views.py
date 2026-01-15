from django.db.models import Count
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response

from annotations.models import Collection, Tag
from belege.models import Beleg


@extend_schema(responses=dict)
@api_view(["get"])
def collection_by_beleg_count(request):
    data = (
        Collection.objects.annotate(item_count=Count("beleg"))
        .order_by("-item_count")[:25]
        .values_list("id", "title", "item_count")
    )
    payload = [{"id": x[0], "value": x[1], "item_count": x[2]} for x in data]

    return Response({"title": "Collection nach Belegen", "payload": payload})


@extend_schema(responses=dict)
@api_view(["get"])
def beleg_by_collection(request):
    data = (
        Beleg.objects.annotate(item_count=Count("collection"))
        .order_by("-item_count")[:25]
        .values_list("dboe_id", "hauptlemma", "item_count")
    )
    payload = [{"id": x[0], "value": x[1], "item_count": x[2]} for x in data]

    return Response({"title": "Belege nach Collections", "payload": payload})


@extend_schema(responses=dict)
@api_view(["get"])
def tag_by_beleg(request) -> dict:
    data = (
        Tag.objects.annotate(item_count=Count("belege"))
        .order_by("-item_count")[:25]
        .values_list("id", "name", "item_count")
    )
    payload = [{"id": x[0], "value": x[1], "item_count": x[2]} for x in data]

    return Response({"title": "Tags nach Belegen", "payload": payload})
