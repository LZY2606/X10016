"""Functions for parsing Links and attribute blocks"""

__all__ = (
    "parseLinkDestination",
    "parseLinkLabel",
    "parseLinkTitle",
    "parse_attrs_block",
)
from .parse_attrs import parse_attrs_block
from .parse_link_destination import parseLinkDestination
from .parse_link_label import parseLinkLabel
from .parse_link_title import parseLinkTitle
