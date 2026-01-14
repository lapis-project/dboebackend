class PopulateLabelMixin:
    """Mixin to automatically populate field labels from model verbose_name."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            source = getattr(field, "source", field_name)
            if source and source != "*":
                try:
                    model_field = self.Meta.model._meta.get_field(source)
                    if (
                        hasattr(model_field, "verbose_name")
                        and model_field.verbose_name
                    ):
                        field.label = model_field.verbose_name
                except Exception:
                    pass
