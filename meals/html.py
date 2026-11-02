import re
from html import unescape

import nh3


def _filter_attribute(tag, name, value):
    if name in {"src", "href"} and value.lstrip().lower().startswith("data:"):
        if (
            tag == "img"
            and name == "src"
            and re.fullmatch(
                r"data:image/(?:jpeg|png|gif|webp);base64,[A-Za-z0-9+/=\s]+",
                value,
                flags=re.IGNORECASE,
            )
        ):
            return value
        return None
    return value


def sanitize_menu_html(value, *, images=False):
    tags = {
        "p",
        "div",
        "br",
        "strong",
        "b",
        "em",
        "i",
        "u",
        "s",
        "span",
        "a",
        "ul",
        "ol",
        "li",
        "blockquote",
    }
    if images:
        tags.add("img")
    return nh3.clean(
        value,
        tags=tags,
        clean_content_tags={
            "script",
            "style",
            "iframe",
            "object",
            "svg",
            "math",
            "template",
        },
        attributes={"*": {"style"}, "a": {"href", "title"}, "img": {"src", "alt"}},
        allowed_classes={
            "p": {"ql-align-center", "ql-align-right", "ql-align-justify"},
            "div": {"ql-align-center", "ql-align-right", "ql-align-justify"},
            "span": {"ql-cursor"},
        },
        filter_style_properties={"color", "background-color", "text-align"},
        url_schemes={"http", "https", "mailto", "data"},
        attribute_filter=_filter_attribute,
    )


def menu_background(value):
    cleaned = sanitize_menu_html(value, images=True)
    match = re.search(r'<img\b[^>]*\bsrc="([^"]+)"', cleaned)
    return unescape(match[1]) if match else None
