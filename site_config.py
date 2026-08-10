#!/usr/bin/env python3
"""Authority-aware public configuration for SAVEONSUB.

This file deliberately distinguishes known public contact channels from pending
or protected values. It is safe for generators to import. Payment destinations,
legal-entity claims and commerce UI must never be enabled here without dated
authority evidence and passing release gates.
"""
from __future__ import annotations

import html
from urllib.parse import quote

SUPPORT_EMAIL = "support@saveonsub.com"
ORDERS_EMAIL = "orders@saveonsub.com"

# CEO Foundation Decisions 2026-07-26: dedicated SAVEONSUB WhatsApp number is
# pending; do not publish a CTA number until procured/approved.
WHATSAPP_STATUS = "pending"
WHATSAPP_NUMBER = None
WHATSAPP_URL = None

# Methods are part of the intended operating model, but destinations/numbers are
# still protected and unverified. Never render a payment destination from this
# config until PAYMENT_DESTINATIONS_STATUS becomes verified via authority input.
PAYMENT_METHODS = ("bKash", "Nagad", "Rocket", "Bank transfer")
PAYMENT_DESTINATIONS_STATUS = "unverified"
PAYMENT_DESTINATIONS = {}

# Exact legal operator wording is not established by current primary evidence.
LEGAL_OPERATOR_STATUS = "unverified"
LEGAL_OPERATOR_PUBLIC = None

# Until provider eligibility, SAVEONSUB prices, payment destinations and launch
# state all pass release validation, generated public navigation must not expose
# checkout/order controls. This is a UI consequence of authority, not the source
# of authority; validate_release.py remains the hard release gate.
COMMERCE_UI_ENABLED = False


def support_mailto(subject: str = "SAVEONSUB support") -> str:
    return f"mailto:{SUPPORT_EMAIL}?subject={quote(subject)}"


def orders_mailto(subject: str = "SAVEONSUB order enquiry") -> str:
    return f"mailto:{ORDERS_EMAIL}?subject={quote(subject)}"


def support_link(label: str = "Email support", subject: str = "SAVEONSUB support") -> str:
    return f'<a href="{html.escape(support_mailto(subject), quote=True)}">{html.escape(label)}</a>'


def contact_cta(label: str = "Contact support", subject: str = "SAVEONSUB support", css_class: str = "btn btn-primary") -> str:
    return (
        f'<a class="{html.escape(css_class, quote=True)}" '
        f'href="{html.escape(support_mailto(subject), quote=True)}">'
        f'{html.escape(label)}</a>'
    )


def payment_methods_text() -> str:
    return ", ".join(PAYMENT_METHODS)
