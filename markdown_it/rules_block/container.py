# Container blocks, e.g.
#
# ::::note {#n1 .lead title="Heads up"}
# content
# ::::
from __future__ import annotations

import logging
from typing import NamedTuple

from ..helpers.parse_attrs import (
    AttrEntry,
    build_attrs,
    is_attr_name_char,
    parse_attrs_block,
)
from .state_block import StateBlock

LOGGER = logging.getLogger(__name__)


class _OpenMarker(NamedTuple):
    marker_len: int
    """Number of colons in the opening marker."""
    name: str
    """Container name (may be empty)."""
    entries: list[AttrEntry]
    """Parsed attribute block entries (empty if no block present)."""
    has_label: bool
    """True if the marker line carries a name and/or an attribute block.

    Lines with only a colon run (and whitespace) are potential closing
    markers rather than opening ones.
    """
    info_pos: int
    """Source position just after the opening colon run."""


def _parse_open_marker(state: StateBlock, line: int) -> _OpenMarker | None:
    """Validate a container opening marker on ``line``.

    The line must hold only a run of 3+ colons, an optional name, an
    optional ``{...}`` attribute block and whitespace.
    """
    pos = state.bMarks[line] + state.tShift[line]
    maximum = state.eMarks[line]

    if pos + 3 > maximum or state.src[pos] != ":":
        return None

    pos = state.skipCharsStr(pos, ":")
    marker_len = pos - (state.bMarks[line] + state.tShift[line])
    info_pos = pos

    pos = state.skipSpaces(pos)

    # optional name
    start = pos
    while pos < maximum and is_attr_name_char(state.src[pos]):
        pos += 1
    name = state.src[start:pos]

    pos = state.skipSpaces(pos)

    # optional attribute block
    entries: list[AttrEntry] = []
    has_attrs = False
    if pos < maximum and state.src[pos] == "{":
        parsed = parse_attrs_block(state.src, pos, maximum)
        if parsed is None:
            return None
        entries, pos = parsed
        has_attrs = True
        pos = state.skipSpaces(pos)

    if pos < maximum:
        # anything else on the line means this is not an opening marker
        return None

    return _OpenMarker(marker_len, name, entries, bool(name) or has_attrs, info_pos)


def container(state: StateBlock, startLine: int, endLine: int, silent: bool) -> bool:
    LOGGER.debug(
        "entering container: %s, %s, %s, %s", state, startLine, endLine, silent
    )

    if state.is_code_block(startLine):
        return False

    marker = _parse_open_marker(state, startLine)
    if marker is None:
        return False

    # Since start is found, we can report success here in validation mode
    if silent:
        return True

    # Search the end of the block, tracking nested containers with a stack
    # of opening marker lengths. A bare colon run closes the innermost
    # container whose opening marker is not longer than the run.
    haveEndMarker = False
    stack = [marker.marker_len]
    nextLine = startLine + 1

    while nextLine < endLine:
        pos = state.bMarks[nextLine] + state.tShift[nextLine]
        maximum = state.eMarks[nextLine]

        if pos < maximum and state.sCount[nextLine] < state.blkIndent:
            # non-empty line with negative indent should stop the block
            break

        if not state.is_code_block(nextLine):
            nested = _parse_open_marker(state, nextLine)
            if nested is not None:
                if nested.has_label:
                    stack.append(nested.marker_len)
                elif nested.marker_len >= stack[-1]:
                    stack.pop()
                    if not stack:
                        haveEndMarker = True
                        break
                # a shorter bare colon run is ordinary content

        nextLine += 1

    markup = ":" * marker.marker_len
    info = state.src[marker.info_pos : state.eMarks[startLine]]

    oldParentType = state.parentType
    state.parentType = "container"

    base_classes = ["container"]
    if marker.name:
        base_classes.append(f"container-{marker.name}")

    lines = [startLine, 0]
    token = state.push("container_open", "div", 1)
    token.markup = markup
    token.info = info
    token.meta = {"name": marker.name}
    token.attrs = build_attrs(marker.entries, base_classes)
    token.map = lines

    state.md.block.tokenize(state, startLine + 1, nextLine)

    token = state.push("container_close", "div", -1)
    token.markup = markup

    state.parentType = oldParentType
    state.line = nextLine + (1 if haveEndMarker else 0)
    lines[1] = state.line

    return True
