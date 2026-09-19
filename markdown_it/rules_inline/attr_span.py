# Process [span text]{#id .class key=value}

from __future__ import annotations

from ..helpers.parse_attrs import parse_attrs
from .state_inline import StateInline


def attr_span(state: StateInline, silent: bool) -> bool:
    start = state.pos
    maximum = state.posMax

    if state.src[start] != "[":
        return False

    labelStart = start + 1
    labelEnd = state.md.helpers.parseLinkLabel(state, start, True)

    # parser failed to find ']', so it's not a valid span
    if labelEnd < 0:
        return False

    pos = labelEnd + 1

    if pos >= maximum or state.src[pos] != "{":
        return False

    parsed = parse_attrs(state.src, pos, maximum)
    if parsed is None:
        return False

    # We found the end of the span, and know for a fact it's a valid span
    # so all that's left to do is to call tokenizer.
    if not silent:
        state.pos = labelStart
        state.posMax = labelEnd

        token = state.push("span_open", "span", 1)
        token.attrs.update(parsed.attrs)

        state.md.inline.tokenize(state)

        token = state.push("span_close", "span", -1)

    state.pos = parsed.end
    state.posMax = maximum
    return True
