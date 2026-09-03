#!/usr/bin/env python3
"""Canonical non-secret SaveOnSub website constants.

Customer-facing generators and guards should import from here instead of
retyping identity/contact values. Never put credentials, supplier cost, customer
data or private business intelligence in this public module.
"""

CONFIG_VERSION = "2026-09-03"
BRAND_NAME = "SaveOnSub"
BRAND_DOMAIN = "saveonsub.com"
SITE_URL = "https://saveonsub.com"

SUPPORT_PHONE_E164 = "+8801305869242"
SUPPORT_PHONE_DIGITS = "8801305869242"
SUPPORT_PHONE_DISPLAY = "+880 1305-869242"
SUPPORT_PHONE_BN_DISPLAY = "+৮৮০ ১৩০৫-৮৬৯২৪২"
WHATSAPP_URL = f"https://wa.me/{SUPPORT_PHONE_DIGITS}"

# The website currently uses the same public number for checkout payment
# instructions and human support. If this changes, update it here first and
# migrate/verify every customer-facing page before publishing.
PAYMENT_PHONE_E164 = SUPPORT_PHONE_E164
PAYMENT_PHONE_DISPLAY = SUPPORT_PHONE_DISPLAY

SUPPORT_EMAIL = "support@saveonsub.com"
LOCALE_PRIMARY = "en-BD"
LOCALE_SECONDARY = "bn-BD"
BUSINESS_TIMEZONE = "Asia/Dhaka"

BRAND_LOCK_DATE = "2026-08-19"
BRAND_LOCK_MARKER = f'data-brand-lock="{BRAND_LOCK_DATE}-approved"'
