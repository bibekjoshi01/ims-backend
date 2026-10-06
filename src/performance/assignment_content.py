"""The small, shared document schema used by assignment instructions."""

import json

from django.core.exceptions import ValidationError

MAX_DESCRIPTION_TEXT = 20000
MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
MAX_ASSIGNMENT_ATTACHMENTS = 5
ATTACHMENT_EXTENSIONS = (
    "pdf",
    "doc",
    "docx",
    "odt",
    "xls",
    "xlsx",
    "ods",
    "ppt",
    "pptx",
    "txt",
    "csv",
    "zip",
    "jpg",
    "jpeg",
    "png",
    "webp",
)


def validate_assignment_description(value):
    """Accept only basic document nodes, with no HTML, URLs or executable attributes."""
    if value == {}:
        return
    message = "Use paragraphs, headings, bold text and lists for the task description."

    def reject():
        raise ValidationError(message)

    if not isinstance(value, dict) or value.get("type") != "doc":
        reject()
    nodes = 0
    text_length = 0
    blocks = {"paragraph", "heading", "bulletList", "orderedList"}

    def visit(node, depth=0):
        nonlocal nodes, text_length
        nodes += 1
        if depth > 12 or nodes > 2000 or not isinstance(node, dict):
            reject()
        kind = node.get("type")
        if not isinstance(kind, str):
            reject()
        if kind == "text":
            if set(node) - {"type", "text", "marks"} or not isinstance(node.get("text"), str):
                reject()
            if not node["text"]:
                reject()
            marks = node.get("marks", [])
            if not isinstance(marks, list) or any(mark != {"type": "bold"} for mark in marks):
                reject()
            text_length += len(node["text"])
            return
        if kind == "hardBreak":
            if set(node) != {"type"}:
                reject()
            return
        if kind not in {"doc", "listItem", *blocks} or set(node) - {"type", "content", "attrs"}:
            reject()
        attrs = node.get("attrs", {})
        if not isinstance(attrs, dict):
            reject()
        if kind == "heading":
            if set(attrs) != {"level"} or attrs["level"] not in (2, 3):
                reject()
        elif kind == "orderedList":
            if set(attrs) - {"start", "type"} or attrs.get("type") is not None:
                reject()
            start = attrs.get("start", 1)
            if type(start) is not int or not 1 <= start <= 10000:
                reject()
        elif attrs:
            reject()
        children = node.get("content", [])
        if not isinstance(children, list):
            reject()
        allowed = (
            {"text", "hardBreak"}
            if kind in {"paragraph", "heading"}
            else {"listItem"}
            if kind in {"bulletList", "orderedList"}
            else blocks
        )
        if kind in {"bulletList", "orderedList", "listItem"} and not children:
            reject()
        if kind == "listItem" and (
            not isinstance(children[0], dict) or children[0].get("type") != "paragraph"
        ):
            reject()
        for child in children:
            if (
                not isinstance(child, dict)
                or not isinstance(child.get("type"), str)
                or child["type"] not in allowed
            ):
                reject()
            visit(child, depth + 1)

    visit(value)
    if text_length > MAX_DESCRIPTION_TEXT or len(json.dumps(value, ensure_ascii=False)) > 100000:
        raise ValidationError("Keep the task description under 20,000 characters.")
