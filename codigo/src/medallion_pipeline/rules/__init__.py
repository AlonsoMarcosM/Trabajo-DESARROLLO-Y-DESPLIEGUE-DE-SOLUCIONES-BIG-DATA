"""
rules/__init__.py
=================
Unified entry point — import all rule sets from a single location.

Usage in transformation scripts:
    from rules import get_customer_rules, get_usage_rules, ...
"""

from .customers import (
    get_customer_rules,
    get_usage_rules,
    get_label_rules,
    get_interaction_rules,
)

__all__ = [
    "get_customer_rules",
    "get_usage_rules",
    "get_label_rules",
    "get_interaction_rules",
]
