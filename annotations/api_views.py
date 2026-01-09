from copy import deepcopy
from typing import Dict

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Count, Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Q, Search
from rest_framework import filters, pagination, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view
from rest_framework.permissions import DjangoObjectPermissions
from rest_framework.response import Response

from belege.models import Beleg
from dboeannotation.metadata import PROJECT_METADATA as PM

from .filters import (
    AnnotationFilter,
    CategoryFilter,
    CollectionFilter,
    EditOfArticleFilter,
    LemmaFilter,
    TagFilter,
    UserFilter,
)
from .models import (
    Annotation,
    Autor_Artikel,
    Category,
    Collection,
    Edit_of_article,
    Es_document,
    Lemma,
    Tag,
)
from .serializers import (
    AnnotationSerializer,
    AutorArtikelSerializer,
    CategorySerializer,
    CollectionSerializer,
    EditOfArticleLemmaSerializer,
    EditOfArticleSerializer,
    EditOfArticleStSerializer,
    EditOfArticleUserSerializer,
    Es_documentListSerializer,
    Es_documentSerializer,
    Es_documentSerializerForCache,
    Es_documentSerializerForScans,
    LemmaSerializer,
    TagSerializer,
    UserListSerializer,
    UserSerializer,
)

# AnonymousUser can view objects if granted 'view' permission


class DjangoObjectPermissionsOrAnonReadOnly(DjangoObjectPermissions):
    authenticated_users_only = False


class CustomObtainAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        response = super(CustomObtainAuthToken, self).post(request, *args, **kwargs)
        token = Token.objects.get(key=response.data["token"])
        return Response({"token": token.key, "id": token.user_id})


class LargeResultsSetPagination(pagination.PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 10000


class UserViewSet(viewsets.ModelViewSet):
    """
    get:
    Return a list of all the existing users.

    post:
    Create a new user instance.

    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    pagination_class = LargeResultsSetPagination
    # authentication_classes = (TokenAuthentication, )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = UserFilter

    def get_serializer_class(self):
        if self.action == "list":
            return UserListSerializer
        return UserSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    """
        get:
        Return a list of all the existing categories.

        post:
    Create a new category instance.

    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = LargeResultsSetPagination
    # authentication_classes = (TokenAuthentication, )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = CategoryFilter


class TagViewSet(viewsets.ModelViewSet):
    """
        get:
        Return a list of all tags.

        post:
    Create a new tag instance.

    """

    queryset = Tag.objects.annotate(
        belege_ids=ArrayAgg("belege__dboe_id", distinct=True)
    ).annotate(belege_count=Count("belege"))
    serializer_class = TagSerializer
    pagination_class = LargeResultsSetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TagFilter


class LemmaViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        queryset = Lemma.objects.all()
        parameter = self.request.query_params.get("has_collection", None)
        editor_para = self.request.query_params.get("has_editor", None)
        if parameter is not None and editor_para is None:
            queryset = Lemma.objects.exclude(
                id__in=Collection.objects.exclude(lemma_id__isnull=True)
            )
        elif parameter is None and editor_para is not None:
            queryset = Lemma.objects.exclude(
                id__in=Edit_of_article.objects.filter(lemma__isnull=False)
            )
        return queryset

    queryset = Lemma.objects.all()
    serializer_class = LemmaSerializer
    pagination_class = LargeResultsSetPagination
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = LemmaFilter


class EditOfArticleViewSet(viewsets.ModelViewSet):
    queryset = Edit_of_article.objects.all()
    serializer_class = EditOfArticleSerializer
    pagination_class = LargeResultsSetPagination
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = EditOfArticleFilter

    def get_serializer_class(self):
        parameter = self.request.query_params.get("reporting")
        if parameter is None:
            return EditOfArticleSerializer
        elif parameter == "0":
            return EditOfArticleStSerializer
        elif parameter == "1":
            return EditOfArticleLemmaSerializer
        elif parameter == "2":
            return EditOfArticleUserSerializer


class AutorArtikelViewSet(viewsets.ModelViewSet):
    queryset = Autor_Artikel.objects.all()
    serializer_class = AutorArtikelSerializer
    pagination_class = LargeResultsSetPagination
    filter_backends = (DjangoFilterBackend,)


class Es_documentViewSet(viewsets.ModelViewSet):
    """
    get:
    Return a list of all the existing documents.

    post:
    Create a new document instance.

    patch:
    Update only certain fields

    """

    queryset = Es_document.objects.all()
    serializer_class = Es_documentSerializer
    pagination_class = LargeResultsSetPagination
    # authentication_classes = (TokenAuthentication, )
    filter_backends = (DjangoFilterBackend,)
    # make a custom filter with exact match for es_id

    # es_id__starts_with = django_filters.CharFilter(lookup_expr='istartswith', field_name="es_id")
    filter_fields = ("es_id", "index", "version", "in_collections", "tag")

    # filterset_class = Es_Document_es_id_filter
    def get_queryset(self):
        qs = super().get_queryset()
        es = str(self.request.query_params.get("es_id__startswith")).lower()
        if isinstance(es, str) and len(es) > 1 and es != "none":
            return qs.filter(es_id__istartswith=es)
        if bool(self.request.query_params.get("cache_only")) is True:
            return qs.exclude(xml="")
        return qs

    def get_serializer_class(self):
        es = str(self.request.query_params.get("es_id__startswith")).lower()
        if isinstance(es, str) and len(es) > 1 and es != "none":
            return Es_documentSerializerForScans
        if bool(self.request.query_params.get("cache_only")) is True:
            return Es_documentSerializerForCache
        return Es_documentSerializer

    def create(self, request, *args, **kwargs):
        many = True if isinstance(self.request.data, list) else False
        if not many:
            return super().create(request, *args, **kwargs)
        else:
            serializer = Es_documentListSerializer(
                data=request.data, context={"request": request}, many=True
            )
            if serializer.is_valid():
                # 	print('is valido')
                serializer.save()
                # 	print('we created something...', serializer)
                return Response(data=serializer.data, status=status.HTTP_201_CREATED)
            else:
                # 	print('is not valido')
                return Response(
                    data=serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )

    def partial_update(self, request, *args, **kwargs):
        allowed_props = {"xml", "xml_error_message"}
        if request.data.keys() <= allowed_props:
            es_document = self.get_object()
            serializer = Es_documentSerializer(
                es_document,
                data=request.data,
                context={"request": request},
                partial=True,
            )
            if serializer.is_valid():
                serializer.save()
                return Response(data=serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"detail": serializer.errors}, status=status.HTTP_409_CONFLICT
                )
        else:
            return Response(
                {"detail": f"Allowed properties are {str(allowed_props)}"},
                status=status.HTTP_409_CONFLICT,
            )

    def put(self, request):
        es_documents_data = request.data
        for es_document_item in es_documents_data:
            try:
                es_document = Es_document.objects.get(es_id=es_document_item["es_id"])
            except Es_document.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

            serializer = self.serializer_class(
                es_document,
                data=es_document_item,
                context={"request": request},
                partial=True,
            )
            if serializer.is_valid():
                serializer.save()

        return Response(status=status.HTTP_200_OK)


class CollectionViewSet(viewsets.ModelViewSet):
    queryset = (
        Collection.objects.annotate(beleg_count=Count("beleg"))
        .select_related("category", "created_by", "lemma_id")
        .prefetch_related(
            Prefetch(
                "beleg",
                queryset=Beleg.objects.with_related(),
            ),
            "curator",
            "es_document",
            "es_document__tag",
            "annotations",
        )
    )
    serializer_class = CollectionSerializer
    pagination_class = LargeResultsSetPagination
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = CollectionFilter

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    # def list(self, request, *args, **kwargs):
    #     reset_queries()
    #     response = super().list(request, *args, **kwargs)

    #     # Log query information
    #     queries = connection.queries
    #     print(f"\n{'=' * 80}")
    #     print(f"Total queries executed: {len(queries)}")
    #     print(f"{'=' * 80}")

    #     # Group queries by type
    #     query_types = {}
    #     for i, query in enumerate(queries, 1):
    #         sql = query["sql"]
    #         time = query["time"]

    #         # Extract table name
    #         if "FROM" in sql:
    #             table = sql.split("FROM")[1].split()[0].strip('"')
    #         elif "UPDATE" in sql:
    #             table = sql.split("UPDATE")[1].split()[0].strip('"')
    #         else:
    #             table = "unknown"

    #         query_types[table] = query_types.get(table, 0) + 1

    #         # Print first 5 and last 5 queries with details
    #         if i <= 5 or i > len(queries) - 5:
    #             print(f"\nQuery {i} ({time}s) - Table: {table}")
    #             print(f"{sql[:200]}..." if len(sql) > 200 else sql)

    #     print(f"\n{'=' * 80}")
    #     print("Queries by table:")
    #     for table, count in sorted(
    #         query_types.items(), key=lambda x: x[1], reverse=True
    #     ):
    #         print(f"  {table}: {count}")
    #     print(f"{'=' * 80}\n")

    #     return response


class AnnotationViewSet(viewsets.ModelViewSet):
    """
        get:
        Return a list of all the existing annotations.

        post:
    Create a new annotation instance.

    """

    queryset = Annotation.objects.all()
    serializer_class = AnnotationSerializer
    pagination_class = LargeResultsSetPagination
    permission_classes = (DjangoObjectPermissionsOrAnonReadOnly,)
    # authentication_classes = (TokenAuthentication, )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = AnnotationFilter

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


@extend_schema(responses={200: {}})
@api_view()
def dboe_query(request):
    """
    The endpoint to query external elasticsearch index;
    the query matches all fields

    """
    client = Elasticsearch(settings.ES_DBOE)
    q = request.GET.get("q")
    if q:
        my_query = Q("multi_match", query=q, fields=["*"])
        search = Search(using=client, index="dboe").query(my_query)
        count = search.count()
        results = search[0:count].execute()
        results = results.to_dict()
    else:
        results = None
    return Response({"results": results})


@extend_schema(
    parameters=[
        {
            "name": "dboe_id",
            "in": "path",
            "required": True,
            "description": "The ID to search in the Elasticsearch index.",
            "schema": {"type": "string"},
        }
    ],
    responses={200: {}},
)
@api_view()
def dboe_query_by_id(request, dboe_id):
    """
    Search elastic search index by dboe-id

    """
    client = Elasticsearch(settings.ES_DBOE)

    my_query = Q("multi_match", query=dboe_id, fields=["_id"])
    search = Search(using=client, index="dboe").query(my_query)
    count = search.count()
    results = search[0:count].execute()
    results = results.to_dict()

    return Response({"results": results["hits"]["hits"][0]["_source"]})


#################################################################
#                    project info view                          #
#################################################################


@extend_schema(responses={200: Dict[str, str]})
@api_view(["GET"])
def project_info(request):
    """
    returns a dict providing metadata about the current project
    """

    info_dict = deepcopy(PM)
    info_dict["base_tech"] = "django rest framework"
    return Response(info_dict)
