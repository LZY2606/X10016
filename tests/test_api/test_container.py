"""Token-level tests for the ``container`` block rule."""

from __future__ import annotations

import pytest

from markdown_it import MarkdownIt
from markdown_it.rules_block.container import container
from markdown_it.rules_block.state_block import StateBlock
from markdown_it.tree import SyntaxTreeNode


def make_md(**options):
    return MarkdownIt("commonmark", options or None).enable(["container", "attr_span"])


def test_container_tokens():
    md = make_md()
    tokens = md.parse('::::note {#n1 .lead title="Heads up"}\nok\n::::\n')
    assert [t.type for t in tokens] == [
        "container_open",
        "paragraph_open",
        "inline",
        "paragraph_close",
        "container_close",
    ]
    open_token, close_token = tokens[0], tokens[-1]
    assert open_token.tag == close_token.tag == "div"
    assert open_token.nesting == 1
    assert close_token.nesting == -1
    assert open_token.markup == close_token.markup == "::::"
    assert open_token.info == 'note {#n1 .lead title="Heads up"}'
    assert open_token.meta == {"name": "note"}
    assert open_token.attrs == {
        "class": "container container-note lead",
        "id": "n1",
        "title": "Heads up",
    }
    # [opening line, line after the container end)
    assert open_token.map == [0, 3]
    assert close_token.map is None


def test_container_levels():
    md = make_md()
    tokens = md.parse("> ::::a\n> :::b\n> x\n> :::\n> ::::\n")
    assert [(t.type, t.nesting, t.level) for t in tokens] == [
        ("blockquote_open", 1, 0),
        ("container_open", 1, 1),
        ("container_open", 1, 2),
        ("paragraph_open", 1, 3),
        ("inline", 0, 4),
        ("paragraph_close", -1, 3),
        ("container_close", -1, 2),
        ("container_close", -1, 1),
        ("blockquote_close", -1, 0),
    ]


def test_container_info_not_stripped():
    md = make_md()
    tokens = md.parse("::: note  {.k}  \nx\n:::\n")
    assert tokens[0].info == " note  {.k}  "
    assert tokens[0].meta == {"name": "note"}
    assert tokens[0].markup == ":::"


def test_container_without_name():
    md = make_md()
    tokens = md.parse(":::\nx\n:::\n")
    open_token = tokens[0]
    assert open_token.meta == {"name": ""}
    assert open_token.info == ""
    assert open_token.attrs == {"class": "container"}


def test_container_attrs_ordering_and_duplicates():
    md = make_md()
    tokens = md.parse(':::n {#a #b .x k=1 .y k=2 j="v"}\nx\n:::\n')
    attrs = tokens[0].attrs
    # class first, other keys in order of first appearance, last value wins
    assert list(attrs.keys()) == ["class", "id", "k", "j"]
    assert attrs == {
        "class": "container container-n x y",
        "id": "b",
        "k": "2",
        "j": "v",
    }


def test_container_map_unclosed():
    md = make_md()
    tokens = md.parse(":::note\nx\n")
    assert tokens[0].type == "container_open"
    assert tokens[0].map == [0, 2]
    assert tokens[-1].type == "container_close"


def test_container_map_empty():
    md = make_md()
    tokens = md.parse(":::note\n:::\nafter\n")
    assert [t.type for t in tokens[:2]] == ["container_open", "container_close"]
    assert tokens[0].map == [0, 2]
    assert (
        md.render(":::note\n:::\n") == '<div class="container container-note"></div>\n'
    )


def test_container_nested_maps():
    md = make_md()
    tokens = md.parse("::::outer\n:::inner\nx\n:::\n::::\n")
    assert tokens[0].map == [0, 5]
    assert tokens[1].map == [1, 4]
    # inner block tokens keep absolute line numbers
    assert tokens[2].map == [2, 3]


def test_container_silent_mode_pushes_no_tokens():
    md = make_md()
    tokens = []
    state = StateBlock(":::note\nx\n:::\n", md, {}, tokens)
    assert container(state, 0, state.lineMax, True) is True
    assert tokens == []


@pytest.mark.parametrize(
    "src",
    [
        ":::note junk\nx\n:::\n",  # trailing text on the opening line
        ":::note {bad!!}\nx\n:::\n",  # invalid attribute block
        ":::note {.k\nx\n:::\n",  # unclosed attribute block
        "::\nx\n::\n",  # too few colons
    ],
)
def test_container_invalid_opening_line(src):
    md = make_md()
    tokens = []
    state = StateBlock(src, md, {}, tokens)
    assert container(state, 0, state.lineMax, False) is False
    assert tokens == []
    assert state.line == 0


def test_container_indented_code_block():
    md = make_md()
    tokens = md.parse("    :::note\n    x\n")
    assert [t.type for t in tokens] == ["code_block"]


def test_container_interrupts_paragraph():
    md = make_md()
    tokens = md.parse("para\n:::note\nx\n:::\n")
    assert [t.type for t in tokens] == [
        "paragraph_open",
        "inline",
        "paragraph_close",
        "container_open",
        "paragraph_open",
        "inline",
        "paragraph_close",
        "container_close",
    ]


def test_container_tree():
    md = make_md()
    tree = SyntaxTreeNode(md.parse(":::note\nx *y*\n:::\n"))
    assert tree.type == "root"
    assert tree.children[0].type == "container"
    assert tree.children[0].children[0].type == "paragraph"


def test_container_enable_disable():
    md = MarkdownIt("commonmark")
    src = ":::note\nx\n:::\n"
    assert "<div" not in md.render(src)
    md.enable("container")
    assert "<div" in md.render(src)
    md.disable("container")
    assert "<div" not in md.render(src)


@pytest.mark.parametrize("preset", ["commonmark", "zero", "gfm-like"])
def test_container_disabled_by_default(preset):
    md = MarkdownIt(preset)
    src = ":::note\nx\n:::\n\n[a]{.k}\n"
    assert "<div" not in md.render(src)
    assert "<span" not in md.render(src)


def test_container_linkify_ignores_attr_values():
    md = MarkdownIt("commonmark", {"linkify": True}).enable(["container", "linkify"])
    result = md.render(':::n {u="http://example.com"}\nx\n:::\n')
    assert '<div class="container container-n" u="http://example.com">' in result
    assert "<a " not in result


def test_container_typographer_ignores_attr_values():
    md = MarkdownIt("commonmark", {"typographer": True}).enable(
        ["container", "replacements", "smartquotes"]
    )
    result = md.render(':::n {t="a--b ..."}\nx\n:::\n')
    assert 't="a--b ..."' in result


def test_container_html_option_off_still_renders():
    md = MarkdownIt("commonmark", {"html": False}).enable(["container", "attr_span"])
    result = md.render(":::note\n[a]{.k}\n:::\n")
    assert result == (
        '<div class="container container-note">\n'
        '<p><span class="k">a</span></p>\n'
        "</div>\n"
    )


def test_container_attr_value_escaped():
    md = make_md()
    result = md.render(':::n {t="a<b & c"}\nx\n:::\n')
    assert 't="a&lt;b &amp; c"' in result
