"""Token-level tests for the container block rule and the attr_span inline rule."""

from __future__ import annotations

import pytest

from markdown_it import MarkdownIt
from markdown_it.rules_block.container import container
from markdown_it.rules_block.state_block import StateBlock
from markdown_it.rules_inline.attr_span import attr_span
from markdown_it.rules_inline.state_inline import StateInline
from markdown_it.tree import SyntaxTreeNode


def make_md(**options) -> MarkdownIt:
    return MarkdownIt("commonmark", options or None).enable(["container", "attr_span"])


class TestRuleToggling:
    def test_disabled_by_default(self):
        src = ":::note\nbody\n:::\n\n[text]{.k}\n"
        for preset in ("commonmark", "zero", "gfm-like", "default"):
            md = MarkdownIt(preset)
            assert "<div" not in md.render(src)
            assert "<span" not in md.render(src)

    def test_enable_disable_by_name(self):
        md = MarkdownIt("commonmark")
        md.enable(["container", "attr_span"])
        assert "container" in md.get_active_rules()["block"]
        assert "attr_span" in md.get_active_rules()["inline"]
        md.disable(["container", "attr_span"])
        assert "container" not in md.get_active_rules()["block"]
        assert "attr_span" not in md.get_active_rules()["inline"]
        assert "<div" not in md.render(":::note\nbody\n:::\n")


class TestContainerTokens:
    def test_token_shape(self):
        tokens = make_md().parse('::::note {#n1 .lead title="Heads up"}\nx\n::::\n')
        open_token, close_token = tokens[0], tokens[-1]
        assert open_token.type == "container_open"
        assert open_token.tag == "div"
        assert open_token.nesting == 1
        assert open_token.markup == "::::"
        assert open_token.info == 'note {#n1 .lead title="Heads up"}'
        assert open_token.meta == {"name": "note"}
        assert open_token.attrs == {
            "class": "container container-note lead",
            "id": "n1",
            "title": "Heads up",
        }
        assert open_token.map == [0, 3]
        assert close_token.type == "container_close"
        assert close_token.tag == "div"
        assert close_token.nesting == -1
        assert close_token.markup == "::::"
        assert close_token.map is None

    def test_info_is_not_stripped(self):
        tokens = make_md().parse(":::note  {.k}  \nx\n:::\n")
        assert tokens[0].info == "note  {.k}  "

    def test_name_defaults_to_empty_string(self):
        tokens = make_md().parse("::: {.k}\nx\n:::\n")
        assert tokens[0].meta == {"name": ""}
        assert tokens[0].attrs == {"class": "container k"}

    def test_attrs_ordering_and_duplicates(self):
        tokens = make_md().parse(":::n {b=1 .x a=1 b=2 .y #i1 #i2}\nx\n:::\n")
        assert list(tokens[0].attrs.items()) == [
            ("class", "container container-n x y"),
            ("b", "2"),
            ("a", "1"),
            ("id", "i2"),
        ]

    def test_levels_and_nesting(self):
        tokens = make_md().parse("::::a\n:::b\ninner\n:::\n::::\n")
        assert [(t.type, t.nesting, t.level) for t in tokens] == [
            ("container_open", 1, 0),
            ("container_open", 1, 1),
            ("paragraph_open", 1, 2),
            ("inline", 0, 3),
            ("paragraph_close", -1, 2),
            ("container_close", -1, 1),
            ("container_close", -1, 0),
        ]

    def test_inner_maps_are_absolute(self):
        tokens = make_md().parse("para\n\n:::note\nbody\n:::\n")
        container_open = tokens[3]
        assert container_open.type == "container_open"
        assert container_open.map == [2, 5]
        paragraph_open = tokens[4]
        assert paragraph_open.type == "paragraph_open"
        assert paragraph_open.map == [3, 4]

    def test_empty_container(self):
        tokens = make_md().parse(":::note\n:::\nafter\n")
        assert [t.type for t in tokens] == [
            "container_open",
            "container_close",
            "paragraph_open",
            "inline",
            "paragraph_close",
        ]
        assert tokens[0].map == [0, 2]

    def test_unclosed_container(self):
        tokens = make_md().parse(":::note\nbody\n")
        assert tokens[0].type == "container_open"
        assert tokens[0].map == [0, 2]
        assert tokens[-1].type == "container_close"

    def test_unclosed_container_closed_by_parent_block(self):
        tokens = make_md().parse("> :::note\n> body\n")
        container_open = tokens[1]
        assert container_open.type == "container_open"
        assert container_open.map == [0, 2]

    def test_indented_colons_are_code_block(self):
        tokens = make_md().parse("    :::note\n    body\n")
        assert [t.type for t in tokens] == ["code_block"]

    def test_interrupts_paragraph(self):
        tokens = make_md().parse("para\n:::note\nbody\n:::\n")
        assert tokens[0].type == "paragraph_open"
        assert tokens[3].type == "container_open"

    def test_marker_line_with_trailing_junk_is_not_a_container(self):
        tokens = make_md().parse(":::note extra\nbody\n:::\n")
        assert tokens[0].type == "paragraph_open"

    def test_invalid_attr_block_is_not_a_container(self):
        tokens = make_md().parse(":::note {bad attr!!}\nbody\n:::\n")
        assert tokens[0].type == "paragraph_open"

    def test_silent_mode_pushes_no_tokens(self):
        md = make_md()
        state = StateBlock(":::note\nbody\n:::\n", md, {}, [])
        assert container(state, 0, state.lineMax, True) is True
        assert state.tokens == []

    def test_syntax_tree_node(self):
        md = make_md()
        tree = SyntaxTreeNode(md.parse(":::note\nbody\n:::\n"))
        assert tree.children[0].type == "container"
        assert tree.children[0].children[0].type == "paragraph"

    def test_rendered_with_html_disabled(self):
        md = make_md(html=False)
        assert md.render(":::note\nbody\n:::\n") == (
            '<div class="container container-note">\n<p>body</p>\n</div>\n'
        )

    def test_attr_value_escaping(self):
        md = make_md()
        assert 'title="a&lt;b"' in md.render(':::note {title="a<b"}\nx\n:::\n')

    def test_linkify_ignores_attr_values(self):
        md = make_md(linkify=True).enable("linkify")
        output = md.render(":::note {url=http://example.com}\nx\n:::\n")
        assert 'url="http://example.com"' in output
        assert "<a " not in output

    def test_typographer_ignores_attr_values(self):
        md = make_md(typographer=True).enable(["replacements", "smartquotes"])
        output = md.render(':::note {title="a -- b ..."}\nx\n:::\n')
        assert 'title="a -- b ..."' in output


class TestAttrSpanTokens:
    def _children(self, src: str):
        tokens = make_md().parse(src)
        assert tokens[0].type == "paragraph_open"
        inline = tokens[1]
        assert inline.type == "inline"
        return inline.children

    def test_token_shape(self):
        children = self._children("[文字]{#a .k lang=zh}\n")
        assert [t.type for t in children] == ["span_open", "text", "span_close"]
        open_token, close_token = children[0], children[-1]
        assert open_token.tag == "span"
        assert open_token.nesting == 1
        assert open_token.attrs == {"class": "k", "id": "a", "lang": "zh"}
        assert close_token.tag == "span"
        assert close_token.nesting == -1

    def test_no_class_key_without_classes(self):
        children = self._children("[x]{#a k=v}\n")
        assert children[0].attrs == {"id": "a", "k": "v"}

    def test_content_parsed_as_inline(self):
        children = self._children("[*em*]{.k}\n")
        assert [t.type for t in children] == [
            "span_open",
            "em_open",
            "text",
            "em_close",
            "span_close",
        ]

    def test_levels(self):
        children = self._children("[x]{.k}\n")
        assert [(t.nesting, t.level) for t in children] == [(1, 0), (0, 1), (-1, 0)]

    def test_empty_attr_block(self):
        children = self._children("[x]{}\n")
        assert children[0].type == "span_open"
        assert children[0].attrs == {}

    def test_beats_reference_link(self):
        children = self._children("[foo]{.k}\n\n[foo]: /url\n")
        assert children[0].type == "span_open"

    def test_inline_link_unaffected(self):
        children = self._children("[foo](/u){.k}\n")
        assert children[0].type == "link_open"
        assert children[-1].type == "text"
        assert children[-1].content == "{.k}"

    def test_invalid_attr_block_is_literal_text(self):
        children = self._children("[foo]{bad attr!!}\n")
        assert all(t.type == "text" for t in children)

    def test_silent_mode_pushes_no_tokens(self):
        md = make_md()
        state = StateInline("[foo]{.k}", md, {}, [])
        assert attr_span(state, True) is True
        assert state.tokens == []

    @pytest.mark.parametrize(
        "src",
        [
            "[foo]{bad attr!!}",  # invalid attribute block
            "[foo]",  # no brace after the label
            "[foo",  # no closing bracket
            "[foo]x{.k}",  # brace not directly after the label
        ],
    )
    def test_failure_restores_pos(self, src: str):
        md = make_md()
        state = StateInline(src, md, {}, [])
        assert attr_span(state, False) is False
        assert state.pos == 0
        assert state.tokens == []

    def test_linkify_ignores_attr_values(self):
        md = make_md(linkify=True).enable("linkify")
        output = md.render("[x]{url=http://example.com}\n")
        assert 'url="http://example.com"' in output
        assert "<a " not in output

    def test_typographer_ignores_attr_values(self):
        md = make_md(typographer=True).enable(["replacements", "smartquotes"])
        output = md.render('[x]{title="a -- b ..."}\n')
        assert 'title="a -- b ..."' in output

    def test_attr_value_escaping(self):
        output = make_md().render('[x]{title="a<b"}\n')
        assert 'title="a&lt;b"' in output
