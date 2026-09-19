"""Parse ``{...}`` attribute blocks.

Shared implementation for the block-level ``container`` rule and the
inline ``attr_span`` rule.

An attribute block is a single-line ``{...}`` group holding whitespace
separated entries, each of which is one of:

- ``#name`` - an id
- ``.name`` - a class
- ``key=value`` - an arbitrary attribute, where ``value`` is either a
  double-quoted string (without double quotes or newlines inside) or a
  bare string without whitespace, ``}`` and ``"``

Names and keys consist of ASCII alphanumerics, ``_`` and ``-`` and may
not be empty. If any entry is invalid, the whole ``{...}`` group is not
an attribute block.
"""

from __future__ import annotations

__all__ = ("AttrEntry", "build_attrs", "is_attr_name_char", "parse_attrs_block")

_NAME_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
)

AttrEntry = tuple[str, str, str]
"""A parsed attribute entry: ``(kind, key, value)``.

``kind`` is one of ``"id"`` (``#name``), ``"class"`` (``.name``) or
``"key"`` (``key=value``). ``value`` is empty for ids and classes.
"""


def is_attr_name_char(ch: str) -> bool:
    """Check if ``ch`` is valid in an attribute name or key."""
    return ch in _NAME_CHARS


def parse_attrs_block(
    src: str, pos: int, maximum: int
) -> tuple[list[AttrEntry], int] | None:
    """Parse an attribute block at ``pos`` (``src[pos]`` must be ``{``).

    :param src: source text
    :param pos: position of the opening ``{``
    :param maximum: parsing boundary (attribute blocks never span lines)
    :return: ``(entries, end)`` with ``end`` just past the closing ``}``,
        or ``None`` if the text at ``pos`` is not a valid attribute block
    """
    if pos >= maximum or src[pos] != "{":
        return None
    pos += 1
    entries: list[AttrEntry] = []
    while True:
        while pos < maximum and src[pos] in " \t":
            pos += 1
        if pos >= maximum:
            # unterminated block (a newline ends the line first)
            return None
        ch = src[pos]
        if ch == "}":
            return entries, pos + 1
        if ch == "#" or ch == ".":
            kind = "id" if ch == "#" else "class"
            pos += 1
            start = pos
            while pos < maximum and src[pos] in _NAME_CHARS:
                pos += 1
            if pos == start:
                return None
            entries.append((kind, src[start:pos], ""))
        else:
            start = pos
            while pos < maximum and src[pos] in _NAME_CHARS:
                pos += 1
            if pos == start:
                return None
            key = src[start:pos]
            if pos >= maximum or src[pos] != "=":
                return None
            pos += 1
            if pos < maximum and src[pos] == '"':
                pos += 1
                start = pos
                while pos < maximum and src[pos] not in '"\n':
                    pos += 1
                if pos >= maximum or src[pos] != '"':
                    return None
                value = src[start:pos]
                pos += 1
            else:
                start = pos
                while pos < maximum and src[pos] not in ' \t\n}"':
                    pos += 1
                if pos == start:
                    return None
                value = src[start:pos]
            entries.append(("key", key, value))
        # entries must be separated by whitespace
        if pos < maximum and src[pos] not in " \t}":
            return None


def build_attrs(
    entries: list[AttrEntry], base_classes: list[str] | None = None
) -> dict[str, str | int | float]:
    """Convert parsed attribute entries to a token attrs dict.

    ``class`` always comes first: any ``base_classes``, then every
    ``.name`` (and ``class=value``) entry in order of appearance.
    Remaining keys are inserted in order of first appearance, with
    duplicate keys (including ``#id``) keeping the last value.
    """
    classes: list[str] = list(base_classes) if base_classes else []
    others: dict[str, str] = {}
    for kind, key, value in entries:
        if kind == "class":
            classes.append(key)
        elif kind == "id":
            others["id"] = key
        elif key == "class":
            classes.append(value)
        else:
            others[key] = value
    attrs: dict[str, str | int | float] = {}
    if classes:
        attrs["class"] = " ".join(classes)
    attrs.update(others)
    return attrs
