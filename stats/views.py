from django.db.models import Count
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response

from annotations.models import Collection
from belege.models import Beleg

STATS_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "payload": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": ["integer", "string"]},
                    "item_count": {"type": "integer"},
                },
            },
        },
    },
}


@extend_schema(
    summary="Top 25 Collections by Beleg Count",
    description="Returns the top 25 collections ordered by the number of belege they contain.",
    responses={
        200: OpenApiResponse(
            description="List of collections with their beleg counts",
            response=STATS_RESPONSE_SCHEMA,
        )
    },
)
@api_view(["get"])
def collection_by_beleg_count(request):
    data = (
        Collection.objects.annotate(item_count=Count("beleg"))
        .order_by("-item_count")[:25]
        .values_list("id", "item_count")
    )
    payload = [{"id": x[0], "item_count": x[1]} for x in data]

    return Response({"title": "Collection nach Belegen", "payload": payload})


@extend_schema(
    summary="Top 25 Belege by Collection Count",
    description="Returns the top 25 belege ordered by the number of collections they appear in.",
    responses={
        200: OpenApiResponse(
            description="List of belege with their collection counts",
            response=STATS_RESPONSE_SCHEMA,
        )
    },
)
@api_view(["get"])
def beleg_by_collection(request):
    data = (
        Beleg.objects.annotate(item_count=Count("collection"))
        .order_by("-item_count")[:25]
        .values_list("dboe_id", "item_count")
    )
    payload = [{"id": x[0], "item_count": x[1]} for x in data]

    return Response({"title": "Belege nach Collections", "payload": payload})
