from typing import Iterable

import lxml.etree as ET
from acdh_tei_pyutils.utils import extract_fulltext, extract_fulltext_with_spacing
from django.db import models
from django.db.models.query import QuerySet
from django_jsonform.models.fields import ArrayField


def annotate_text(
    orig_text: str, to_annotate: list[str], tag: str = "em", strip_this: bool = True
) -> str:
    if not to_annotate:
        pass
    else:
        for text in sorted(to_annotate, key=len, reverse=True):
            orig_text = orig_text.replace(
                text,
                f"<{tag}>{text}</{tag}>",
                1,
            )
    if strip_this:
        orig_text = orig_text.replace("this:", "")
    return orig_text.strip()


def populate_fields_from_xml(doc, current_class):
    """Populate `current_class`'s fields from `doc` based on each field's `extra` metadata."""
    for field in current_class._meta.fields:
        if (
            hasattr(field, "extra")
            and "xpath" in field.extra
            and isinstance(field, (models.CharField, models.TextField))
            and not getattr(current_class, field.name)
        ):
            xpath_expr = field.extra["xpath"]
            try:
                nodes = doc.any_xpath(xpath_expr)[0]
            except IndexError:
                continue
            try:
                value = extract_fulltext(nodes)
            except AttributeError:
                value = nodes
            if isinstance(field, models.CharField):
                if field.max_length and len(value) > field.max_length:
                    value = value[: field.max_length]
                    if hasattr(current_class, "import_issue"):
                        current_class.import_issue = True
            if isinstance(field, (models.CharField, models.TextField)):
                value = value.strip()
            setattr(current_class, field.name, value)
        if isinstance(field, ArrayField) and not getattr(current_class, field.name):
            xpath_expr = field.extra["xpath"]
            try:
                nodes = doc.any_xpath(xpath_expr)
            except IndexError:
                continue
            values = []
            for node in nodes:
                try:
                    value = extract_fulltext(node)
                except AttributeError:
                    value = node
                if isinstance(value, str):
                    value = value.strip()
                values.append(value)
            setattr(current_class, field.name, values)
        if (
            hasattr(field, "extra")
            and "xml_element" in field.extra
            and not getattr(current_class, field.name)
        ):
            xpath_expr = field.extra["xml_element"]
            items = []
            for node in doc.any_xpath(xpath_expr):
                items.append(node_to_json(node))
            if items:
                setattr(current_class, field.name, items)


def node_to_json(node: ET.Element) -> dict:
    item = {"text": extract_fulltext_with_spacing(node)}
    for attr_name, attr_value in node.attrib.items():
        item[attr_name.split("}")[-1]] = attr_value
    for child in node:
        tag_name = child.tag.split("}")[-1]
        if child.attrib:
            attributes = "__".join(
                f"{attr_name.split('}')[-1]}_{attr_value}"
                for attr_name, attr_value in sorted(child.attrib.items())
            )
            tag_name = f"{tag_name}__{attributes}"
        item.setdefault(tag_name, []).append(extract_fulltext_with_spacing(child))
    return item


def transform_record(raw: dict) -> dict:
    out = {}
    for key, v in raw.items():
        # Normalize QuerySets explicitly
        if isinstance(v, QuerySet):
            v = list(v)
        # Some Django related managers may appear (e.g. ManyRelatedManager);
        # catch generic iterables except strings/bytes
        elif (
            not isinstance(v, (str, bytes, list, dict))
            and hasattr(v, "__iter__")
            and not isinstance(v, Iterable)  # narrow - safety; Iterable imported
        ):
            # Fallback path (likely not hit often)
            try:
                v = list(v)  # type: ignore[arg-type]
            except Exception:
                pass

        if key == "id":
            # Keep primary key as-is (string)
            out[key] = str(v)
        elif v in ("", None, []):
            out[key] = []
        elif hasattr(v, "exists") and callable(getattr(v, "exists")) and not v.exists():
            out[key] = []
        elif isinstance(v, list):
            # Coerce every element to string for Typesense
            out[key] = [str(x) for x in v if x not in (None, "")]
        else:
            out[key] = [str(v)]
    return out
