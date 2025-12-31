import django_filters
from django.contrib.auth.models import User
from django.db.models import (
    Count,
    ExpressionWrapper,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
)
from django.db.models.functions import Coalesce
from django_filters.widgets import CSVWidget

from .models import Annotation, Category, Collection, Edit_of_article, Lemma, Tag


class UserFilter(django_filters.rest_framework.FilterSet):
    username = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = User
        fields = [
            "username",
        ]


class CategoryFilter(django_filters.rest_framework.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Category
        fields = [
            "name",
        ]


class TagFilter(django_filters.rest_framework.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
    color = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Tag
        fields = ["name", "color"]


class AnnotationFilter(django_filters.rest_framework.FilterSet):
    title = django_filters.CharFilter(lookup_expr="icontains")
    description = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Annotation
        fields = ["title", "description", "collection", "category", "created_by"]


class CollectionFilter(django_filters.rest_framework.FilterSet):
    title = django_filters.CharFilter(lookup_expr="icontains")
    annotations__category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.all(),
        label="Annotation category",
        help_text="Search collections by category of its annotations",
    )
    tag = django_filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name="es_document__tag",
        label="Tag",
        help_text="Filter collections by tags of its documents",
    )
    category = django_filters.ModelMultipleChoiceFilter(
        queryset=Category.objects.filter(
            name__in=[
                "distribution",
                "sense",
                "multi_word_expression",
                "etymology",
                "compound",
                "lemma",
            ],
        ),
        widget=CSVWidget,
        field_name="category__name",
        to_field_name="name",
        method="filter_categories",
    )

    class Meta:
        model = Collection

        fields = {
            "id": ["exact", "contains"],
            "created_by": ["exact"],
            "public": ["exact"],
            "annotations": ["exact"],
            "deleted": ["exact"],
            "lemma_id": ["exact", "isnull"],
        }

    def filter_categories(self, queryset, name, value):
        if value:
            queryset = queryset.filter(category__name__in=value)
        return queryset


class LemmaFilter(django_filters.rest_framework.FilterSet):
    CHOICES_TASK = (
        (0, "Keiner Aufgabe zugewiesen"),
        (1, "Bereits Aufgabe zugewiesen"),
        (2, "Kein User zugewiesen"),
    )

    CHOICES_COLLECTION = (
        (0, "Collection zugewiesen"),
        (1, "Keiner Collection zugewiesen"),
    )

    CHOICES_NORM = ((1, "Hat Normalisierung"), (2, "Keine Normaliserung"))
    org = django_filters.CharFilter(lookup_expr="icontains")
    norm = django_filters.CharFilter(lookup_expr="icontains")
    lemmatisierung = django_filters.CharFilter(lookup_expr="icontains")
    simplex__lemmatisierung = django_filters.CharFilter(lookup_expr="icontains")
    count__gt = django_filters.NumberFilter(field_name="count", lookup_expr="gt")
    count__lt = django_filters.NumberFilter(field_name="count", lookup_expr="lt")
    has__norm = django_filters.ChoiceFilter(
        label="has_norm", method="filter_norm", choices=CHOICES_NORM
    )
    # has__lemma = django_filters.BooleanFilter(field_name='has_lemma', method='check_task')
    task = django_filters.ChoiceFilter(
        label="tasks", method="check_task", choices=CHOICES_TASK
    )
    collection = django_filters.ChoiceFilter(
        label="Collections", method="check_collection", choices=CHOICES_COLLECTION
    )
    users = django_filters.ModelChoiceFilter(
        queryset=User.objects.all(),
        label="users",
        empty_label="All Users",
        method="filter_users",
    )

    def filter_norm(self, queryset, name, value):
        val = int(value)

        if val == 1:
            return queryset.exclude(Q(norm="") | Q(norm__isnull=True))
        elif val == 2:
            return queryset.filter(Q(norm="") | Q(norm__isnull=True))
        return queryset

    def filter_users(self, queryset, name, value):
        return Lemma.objects.filter(
            Q(id__in=Edit_of_article.objects.filter(user_id=value).values("lemma"))
            | Q(
                simplex__in=Edit_of_article.objects.filter(user_id=value).values(
                    "lemma"
                )
            )
        )

    def check_collection(self, queryset, name, value):
        val = int(value)
        blocked = (
            Collection.objects.exclude(lemma_id=None)
            .values_list("lemma_id", flat=True)
            .distinct()
        )

        if val == 1:
            return Lemma.objects.exclude(id__in=blocked)
        else:
            return Lemma.objects.filter(id__in=blocked)

    def check_task(self, queryset, name, value):
        val = int(value)
        blocked = (
            Edit_of_article.objects.exclude(lemma=None)
            .values_list("lemma", flat=True)
            .distinct()
        )
        if val == 0:
            return queryset.exclude(Q(id__in=blocked) | Q(simplex_id__in=blocked))
        elif val == 1:
            return queryset.filter(Q(id__in=blocked) | Q(simplex_id__in=blocked))
        blocked = (
            Edit_of_article.objects.exclude(lemma=None, user=None)
            .values_list("lemma", flat=True)
            .distinct()
        )
        return queryset.exclude(id__in=blocked)

    has__simplex = django_filters.BooleanFilter(
        field_name="simplex", lookup_expr="isnull"
    )

    class Meta:
        model = Lemma
        fields = [
            "org",
            "norm",
            "filename",
            "count",
            "simplex",
            "task",
            "lemmatisierung",
            "users",
            "id",
        ]


class EditOfArticleFilter(django_filters.rest_framework.FilterSet):
    CHOICES_STATUS = (
        (0, "Wurde bereits zugewiesen"),
        (1, "Nur Irrelevant"),
        (2, "Nur bereits vorhandene Aufgaben"),
    )
    CHOICES_REPORT = (
        (0, "Nach Step und Status gruppieren"),
        (1, "Bearbeitete Lemma nach User"),
        (2, "Nach User gruppieren"),
    )
    CHOICES_STEP = (
        (0, "Nach Step Irrelevant oder Status Final Version filtern"),
        (1, "Nicht filtern"),
    )
    reporting = django_filters.ChoiceFilter(
        label="Reporting", method="check_report", choices=CHOICES_REPORT
    )
    user = django_filters.CharFilter(
        field_name="user__username", lookup_expr="icontains"
    )
    lemma = django_filters.CharFilter(
        field_name="lemma__lemmatisierung", lookup_expr="icontains"
    )
    lemma__id = django_filters.CharFilter(field_name="lemma__id", lookup_expr="iexact")
    date = django_filters.DateFilter(field_name="deadline", lookup_expr="exact")
    finished_date = django_filters.DateFromToRangeFilter()
    begin_time = django_filters.DateFromToRangeFilter()
    last_edited = django_filters.DateFromToRangeFilter()
    currentstatus = django_filters.ChoiceFilter(
        label="Filter for Status", method="check_status", choices=CHOICES_STATUS
    )
    mytasks = django_filters.ChoiceFilter(
        label="Nach eigenen Aufgaben filtern",
        method="check_mytasks",
        choices=CHOICES_STEP,
    )

    def check_mytasks(self, queryset, name, value):
        val = int(value)
        entry = queryset.filter(current=True)
        if val == 0:
            return entry.filter(Q(step="IRRELEVANT") | Q(status="FINAL_VERSION"))
        return entry

    def check_report(self, queryset, name, value):
        val = int(value)
        entry = queryset
        if val == 0:
            return entry.values("step", "status").annotate(
                steps=Count("step"), stati=Count("status")
            )
        elif val == 1:
            # simplex_lemma = Lemma.objects.filter(simplex = OuterRef('lemma')).order_by().values('simplex')
            # total_count = simplex_lemma.annotate(total=Sum('count')).values('total')
            es_documents = (
                Collection.objects.filter(
                    lemma_id=OuterRef("lemma"), category__name="lemma"
                )
                .order_by()
                .values("lemma_id_id")
            )
            es_document_total_count = es_documents.annotate(
                docs_count=Count("es_document")
            ).values("docs_count")
            result = entry.values("lemma__lemmatisierung", "user__username").annotate(
                document__count=ExpressionWrapper(
                    Coalesce(Subquery(es_document_total_count), 0),
                    output_field=IntegerField(),
                )
            )
            return result
        elif val == 2:
            return entry.values("user__username").annotate(
                lemma_count=Count("lemma", distinct=True)
            )
        return entry

    def check_status(self, queryset, name, value):
        val = int(value)
        if val == 0:
            return queryset.filter(step="ZUGEWIESEN")
        elif val == 1:
            return queryset.filter(step="IRRELEVANT")
        return queryset.exclude(step="ZUGEWIESEN")

    class Meta:
        model = Edit_of_article
        fields = [
            "deadline",
            "step",
            "status",
            "last_edited",
            "current",
            "user",
            "lemma",
            "finished_date",
            "begin_time",
        ]
