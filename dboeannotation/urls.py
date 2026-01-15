from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from rest_framework import routers
from rest_framework.authtoken import views

from annotations import api_views
from belege import api_views as belege_api_views
from siglen import api_views as siglen_api_views

router = routers.DefaultRouter()
router.register(r"users", api_views.UserViewSet)
router.register(r"categories", api_views.CategoryViewSet)
router.register(r"tags", api_views.TagViewSet)
router.register(r"documents", api_views.Es_documentViewSet)
router.register(r"collections", api_views.CollectionViewSet)
router.register(r"annotations", api_views.AnnotationViewSet)
router.register(r"lemmas", api_views.LemmaViewSet)
router.register(r"author_artikel", api_views.AutorArtikelViewSet)
router.register(r"article_edits", api_views.EditOfArticleViewSet)
router.register(
    r"belege-elastic-search",
    belege_api_views.BelegViewSetElasticSearch,
    basename="belege-elastic-search",
)
router.register(r"kontexte", belege_api_views.CitationViewSet)
router.register(r"lautungen", belege_api_views.LautungViewSet)
router.register(r"lehnworte", belege_api_views.LehnwortViewSet)
router.register(r"facsimiles", belege_api_views.FacsimileViewSet)
router.register(r"facsimiles-belege", belege_api_views.BelegFacsViewset)
router.register(r"siglen", siglen_api_views.SigleViewSet)
router.register(r"belege-siglen", siglen_api_views.BeleSigleViewSet)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("api-token-auth/", views.obtain_auth_token),
    path("authenticate/", api_views.CustomObtainAuthToken.as_view()),
    path("project-info/", api_views.project_info),
    path("api/dboe-query/", api_views.dboe_query),
    path(
        "api/dboe-query-by-id/<str:dboe_id>",
        api_views.dboe_query_by_id,
        name="dboe_query_by_id",
    ),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("belege/", include("belege.urls", namespace="belege")),
    path("stats/", include("stats.urls", namespace="stats")),
    path("", include("webpage.urls", namespace="webpage")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
