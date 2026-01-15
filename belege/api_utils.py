from django.db import models
from django.forms import TextInput
from django_filters import UnknownFieldBehavior
from django_filters import rest_framework as filters

CHAR_LOOKUP_CHOICES = [
    ("icontains", "Contains"),
    ("iexact", "Equals"),
    ("istartswith", "Starts with"),
    ("iendswith", "Ends with"),
]


def get_verbose_name(model, field):
    try:
        return model._meta.get_field(field).verbose_name
    except AttributeError:
        return f"no verbose_name provided for {model}.{field}"


def filter_by_ids(queryset, name, value):
    values = value.split(",")
    return queryset.filter(dboe_id__in=values)


def get_filterset_for_model(model_class, fields=None):
    """Returns a FilterSet class for the given model_class.

    Args:
        model_class: The Django model class to create a filterset for.
        fields: Optional list of field names to include. If None or empty, all fields are processed.
    """
    if fields is None:
        fields = []

    class DynamicFilterSet(filters.FilterSet):
        @classmethod
        def get_filters(cls):
            """Override to add dynamic filters before schema generation."""
            filters_dict = super().get_filters()

            if fields:
                filters_to_remove = [
                    key
                    for key in list(filters_dict.keys())
                    if key not in fields
                    and not key.startswith(tuple(f"{f}__" for f in fields))
                    and key != "ids"
                ]
                for key in filters_to_remove:
                    filters_dict.pop(key, None)

            if hasattr(cls._meta.model, "dboe_id"):
                filters_dict["ids"] = filters.CharFilter(
                    method=filter_by_ids,
                    label="DBOE IDs",
                    help_text="Enter comma-separated DBOE IDs",
                )

            for field in (
                cls._meta.model._meta.fields + cls._meta.model._meta.many_to_many
            ):
                field_name = field.name

                # Skip field if fields list is provided and field is not in it
                if fields and field_name not in fields:
                    continue

                if isinstance(
                    field, (models.CharField, models.TextField, models.BooleanField)
                ):
                    filters_dict[f"{field_name}"] = filters.CharFilter(
                        field_name=field_name,
                        lookup_expr="icontains",
                        label=field.verbose_name,
                        help_text=field.help_text,
                    )
                elif isinstance(field, (models.ForeignKey, models.ManyToManyField)):
                    filters_dict[field_name] = filters.ModelChoiceFilter(
                        field_name=field_name,
                        queryset=field.related_model.objects.all(),
                        label=field.verbose_name,
                        help_text=f"Enter ID for {field.verbose_name}",
                        widget=TextInput(
                            attrs={
                                "placeholder": "Enter ID",
                            }
                        ),
                    )

            return filters_dict

        class Meta:
            model = model_class
            fields = "__all__"
            unknown_field_behavior = UnknownFieldBehavior.IGNORE

    return DynamicFilterSet
