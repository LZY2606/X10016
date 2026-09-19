"""Token-level tests for the ``attr_span`` inline rule."""

from __future__ import annotations

import pytest

from markdown_it import MarkdownIt
from markdown_it.rules_inline.attr_span import attr_span
from markdown_it.rules_inline.state_inline import StateInline


def make_md(**options):
    return MarkdownIt("commonmark", options or None).enable(["container", "attr_span"])


def inline_children(md, src):
    tokens = md.parse(src)
    assert tokens[0].type == "paragraph_open"
    assert tokens[1].type == "inline"
    return tokens[1].children


def test_attr_span_tokens():
    md = make_md()
    children = inline_children(md, "[text]{#a .k lang=zh}\n")
    assert [t.type for t in children] == ["span_open", "text", "span_close"]
    open_token, text_token, close_token = children
    assert open_token.tag == close_token.tag == "span"
    assert open_token.nesting == 1
    assert text_token.nesting == 0
    assert close_token.nesting == -1
    assert open_token.level == 0
    assert text_token.level == 1
    assert close_token.level == 0
    assert open_token.attrs == {"id": "a", "class": "k", "lang": "zh"}
    assert text_token.content == "text"


def test_attr_span_render():
    md = make_md()
    assert md.render("[文字]{#a .k lang=zh}\n") == (
        '<p><span id="a" class="k" lang="zh">文字</span></p>\n'
    )


def test_attr_span_no_class_without_class_entries():
    md = make_md()
    children = inline_children(md, "[a]{#i k=v}\n")
    assert children[0].attrs == {"id": "i", "k": "v"}
    children = inline_children(md, "[a]{}\n")
    assert children[0].attrs == {}


def test_attr_span_class_position_and_duplicates():
    md = make_md()
    children = inline_children(md, "[a]{k=1 .x #i .y k=2}\n")
    attrs = children[0].attrs
    assert list(attrs.keys()) == ["k", "class", "id"]
    assert attrs == {"k": "2", "class": "x y", "id": "i"}


def test_attr_span_nested_inline_content():
    md = make_md()
    children = inline_children(md, "[a *b* `c`]{.k}\n")
    assert [t.type for t in children] == [
        "span_open",
        "text",
        "em_open",
        "text",
        "em_close",
        "text",
        "code_inline",
        "span_close",
    ]


def test_attr_span_silent_mode_pushes_no_tokens():
    md = make_md()
    tokens = []
    state = StateInline("[a]{.k}", md, {}, tokens)
    assert attr_span(state, True) is True
    assert tokens == []
    assert state.pos == len("[a]{.k}")


@pytest.mark.parametrize(
    "src",
    [
        "[a]{bad!!}",  # invalid entry
        "[a]{.k",  # unclosed block
        "[a]{.k\n}",  # attribute block may not span lines
        "[a] {.k}",  # no bracket directly before the brace
        "[a](/u)",  # inline link, not a span
        "[a",  # no closing bracket
    ],
)
def test_attr_span_failure_restores_pos(src):
    md = make_md()
    tokens = []
    state = StateInline(src, md, {}, tokens)
    state.pos = 0
    assert attr_span(state, False) is False
    assert state.pos == 0
    assert tokens == []


def test_attr_span_failure_restores_pos_mid_text():
    md = make_md()
    tokens = []
    state = StateInline("ab[a]{.k", md, {}, tokens)
    state.pos = 2
    assert attr_span(state, False) is False
    assert state.pos == 2


def test_attr_span_beats_reference_link():
    md = make_md()
    result = md.render("[foo]{.k}\n\n[foo]: /u\n")
    assert result == '<p><span class="k">foo</span></p>\n'


def test_attr_span_does_not_capture_inline_link():
    md = make_md()
    result = md.render("[foo](/u){.k}\n")
    assert result == '<p><a href="/u">foo</a>{.k}</p>\n'


def test_attr_span_enable_disable():
    md = MarkdownIt("commonmark")
    src = "[a]{.k}\n"
    assert "<span" not in md.render(src)
    md.enable("attr_span")
    assert "<span" in md.render(src)
    md.disable("attr_span")
    assert "<span" not in md.render(src)


def test_attr_span_linkify_ignores_attr_values():
    md = MarkdownIt("commonmark", {"linkify": True}).enable(["attr_span", "linkify"])
    result = md.render('[a]{u="http://example.com"}\n')
    assert result == '<p><span u="http://example.com">a</span></p>\n'


def test_attr_span_typographer_ignores_attr_values():
    md = MarkdownIt("commonmark", {"typographer": True}).enable(
        ["attr_span", "replacements", "smartquotes"]
    )
    result = md.render('[a]{t="x--y ..."}\n')
    assert result == '<p><span t="x--y ...">a</span></p>\n'


def test_attr_span_html_option_off_still_renders():
    md = MarkdownIt("commonmark", {"html": False}).enable("attr_span")
    assert md.render("[a]{.k}\n") == '<p><span class="k">a</span></p>\n'


def test_attr_span_attr_value_escaped():
    md = make_md()
    result = md.render('[a]{t="x<y"}\n')
    assert result == '<p><span t="x&lt;y">a</span></p>\n'
