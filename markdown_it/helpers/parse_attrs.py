"""Parse a ``{...}`` attribute block, shared by the container and attr_span rules."""

from __future__ import annotations

from collections.abc import Sequence
from typing import NamedTuple

from ..common.utils import isStrSpace


class ParsedAttrs(NamedTuple):
    end: int
    """Position of the first character after the closing ``}``."""

    attrs: dict[str, str]
    """The ordered HTML attributes."""


def _is_name_char(ch: str) -> bool:
    """Check if a character is valid in an attribute name or key."""
    return ch.isascii() and (ch.isalnum() or ch in "_-")


def parse_attrs(
    src: str, pos: int, maximum: int, *, base_classes: Sequence[str] = ()
) -> ParsedAttrs | None:
    """Parse an attribute block starting at ``pos`` (which must point at ``{``).

    The block is a ``{`` followed by whitespace-separated entries and a closing
    ``}`` on the same line. Each entry is one of:

    - ``#name`` - an ``id`` attribute
    - ``.name`` - appended to the ``class`` attribute
    - ``key=value`` - a plain attribute, where ``value`` is either a double
      quoted string (no ``"`` or newline inside) or a bare string without
      whitespace, ``}`` or ``"``

    Names and keys consist of ASCII alphanumerics, ``_`` and ``-`` and may not
    be empty. ``{}`` is a valid, empty block.

    :param src: source text
    :param pos: position of the opening ``{``
    :param maximum: parsing may not proceed past this position
    :param base_classes: classes that initialise the ``class`` attribute,
        before any ``.name`` entries are appended
    :return: the parsed attributes, or ``None`` if the text at ``pos``
        is not a valid attribute block
    """
    if pos >= maximum or src[pos] != "{":
        return None
    pos += 1

    entries: list[tuple[str, str, str]] = []
    while True:
        while pos < maximum and isStrSpace(src[pos]):
            pos += 1
        if pos >= maximum:
            return None
        ch = src[pos]
        if ch == "}":
            pos += 1
            break
        if ch == "#" or ch == ".":
            kind = "id" if ch == "#" else "class"
            pos += 1
            start = pos
            while pos < maximum and _is_name_char(src[pos]):
                pos += 1
            if pos == start:
                return None
            entries.append((kind, kind, src[start:pos]))
        elif _is_name_char(ch):
            start = pos
            while pos < maximum and _is_name_char(src[pos]):
                pos += 1
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
                while pos < maximum and not (
                    isStrSpace(src[pos]) or src[pos] in '}\n"'
                ):
                    pos += 1
                if pos == start:
                    return None
                value = src[start:pos]
            entries.append(("kv", key, value))
        else:
            return None
        # an entry must be followed by whitespace or the closing brace
        if pos < maximum and not (isStrSpace(src[pos]) or src[pos] == "}"):
            return None

    attrs: dict[str, str] = {}
    if base_classes:
        attrs["class"] = " ".join(base_classes)
    for kind, key, value in entries:
        if kind == "class":
            if "class" in attrs:
                attrs["class"] += " " + value
            else:
                attrs["class"] = value
        else:
            # keys are inserted in order of first appearance,
            # duplicates keep the last value
            attrs[key] = value

    return ParsedAttrs(pos, attrs)
