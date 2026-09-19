# Process [text]{#id .class key=value} attribute spans

from ..helpers.parse_attrs import build_attrs, parse_attrs_block
from .state_inline import StateInline


def attr_span(state: StateInline, silent: bool) -> bool:
    if state.src[state.pos] != "[":
        return False

    maximum = state.posMax
    labelStart = state.pos + 1
    labelEnd = state.md.helpers.parseLinkLabel(state, state.pos, True)

    # parser failed to find ']', so it's not a valid span
    if labelEnd < 0:
        return False

    pos = labelEnd + 1
    if pos >= maximum or state.src[pos] != "{":
        return False

    parsed = parse_attrs_block(state.src, pos, maximum)
    if parsed is None:
        return False
    entries, pos = parsed

    if not silent:
        attrs = build_attrs(entries)

        state.pos = labelStart
        state.posMax = labelEnd

        token = state.push("span_open", "span", 1)
        token.attrs = attrs

        state.md.inline.tokenize(state)

        state.push("span_close", "span", -1)

    state.pos = pos
    state.posMax = maximum
    return True
