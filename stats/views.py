from django.db.models import Count
from rest_framework.decorators import api_view
from rest_framework.response import Response

from annotations.models import Collection, Tag
from belege.models import Beleg


@api_view(["get"])
def collection_by_beleg_count(request):
    data = (
        Collection.objects.annotate(item_count=Count("beleg"))
        .order_by("-item_count")[:25]
        .values_list("id", "item_count")
    )
    payload = [{"id": x[0], "item_count": x[1]} for x in data]

    return Response({"title": "Collection nach Belegen", "payload": payload})


@api_view(["get"])
def beleg_by_collection(request):
    data = (
        Beleg.objects.annotate(item_count=Count("collection"))
        .order_by("-item_count")[:25]
        .values_list("dboe_id", "item_count")
    )
    payload = [{"id": x[0], "item_count": x[1]} for x in data]

    return Response({"title": "Belege nach Collections", "payload": payload})


@api_view(["get"])
def tag_by_beleg(request):
    data = (
        Tag.objects.annotate(item_count=Count("belege"))
        .order_by("-item_count")[:25]
        .values_list("id", "item_count")
    )
    payload = [{"id": x[0], "item_count": x[1]} for x in data]

    return Response({"title": "Tags nach Belegen", "payload": payload})
