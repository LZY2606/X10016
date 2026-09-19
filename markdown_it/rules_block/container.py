# Block containers (::: name {#id .class key=value})
from __future__ import annotations

import logging

from ..helpers.parse_attrs import parse_attrs
from .state_block import StateBlock

LOGGER = logging.getLogger(__name__)


def _is_name_char(ch: str) -> bool:
    """Check if a character is valid in a container name."""
    return ch.isascii() and (ch.isalnum() or ch in "_-")


def container(state: StateBlock, startLine: int, endLine: int, silent: bool) -> bool:
    LOGGER.debug(
        "entering container: %s, %s, %s, %s", state, startLine, endLine, silent
    )

    haveEndMarker = False
    pos = state.bMarks[startLine] + state.tShift[startLine]
    maximum = state.eMarks[startLine]

    if state.is_code_block(startLine):
        return False

    if pos + 3 > maximum:
        return False

    if state.src[pos] != ":":
        return False

    # scan the marker length
    mem = pos
    pos = state.skipCharsStr(pos, ":")
    marker_len = pos - mem

    if marker_len < 3:
        return False

    markup = state.src[mem:pos]
    info = state.src[pos:maximum]

    # parse the optional name and attribute block from the rest of the line
    pos = state.skipSpaces(pos)
    start = pos
    while pos < maximum and _is_name_char(state.src[pos]):
        pos += 1
    name = state.src[start:pos]
    pos = state.skipSpaces(pos)

    base_classes = ["container"]
    if name:
        base_classes.append(f"container-{name}")

    parsed = None
    if pos < maximum and state.src[pos] == "{":
        parsed = parse_attrs(state.src, pos, maximum, base_classes=base_classes)
        if parsed is None:
            return False
        pos = state.skipSpaces(parsed.end)

    # only the marker, name, attribute block and whitespace
    # are allowed on the opening line
    if pos != maximum:
        return False

    # Since start is found, we can report success here in validation mode
    if silent:
        return True

    # search for the closing marker
    nextLine = startLine

    while True:
        nextLine += 1
        if nextLine >= endLine:
            # unclosed block should be autoclosed by end of document.
            # also block seems to be autoclosed by end of parent
            break

        pos = mem = state.bMarks[nextLine] + state.tShift[nextLine]
        maximum = state.eMarks[nextLine]

        if pos < maximum and state.sCount[nextLine] < state.blkIndent:
            # non-empty line with negative indent should stop the list:
            # - :::
            #  test
            break

        try:
            if state.src[pos] != ":":
                continue
        except IndexError:
            break

        if state.is_code_block(nextLine):
            continue

        pos = state.skipCharsStr(pos, ":")

        # closing marker must be at least as long as the opening one
        if pos - mem < marker_len:
            continue

        # make sure tail has spaces only
        pos = state.skipSpaces(pos)

        if pos < maximum:
            continue

        haveEndMarker = True
        # found!
        break

    lines = [startLine, 0]

    token = state.push("container_open", "div", 1)
    token.markup = markup
    token.info = info
    if parsed is not None:
        token.attrs.update(parsed.attrs)
    else:
        token.attrs["class"] = " ".join(base_classes)
    token.meta["name"] = name
    token.map = lines

    state.md.block.tokenize(state, startLine + 1, nextLine)

    token = state.push("container_close", "div", -1)
    token.markup = markup

    state.line = nextLine + (1 if haveEndMarker else 0)
    lines[1] = state.line

    return True
