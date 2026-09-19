"""Functions for parsing Links"""

__all__ = (
    "ParsedAttrs",
    "parseLinkDestination",
    "parseLinkLabel",
    "parseLinkTitle",
    "parse_attrs",
)
from .parse_attrs import ParsedAttrs, parse_attrs
from .parse_link_destination import parseLinkDestination
from .parse_link_label import parseLinkLabel
from .parse_link_title import parseLinkTitle
