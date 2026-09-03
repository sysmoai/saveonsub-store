#!/bin/bash
set -e

# The SaveOnSub logo/favicon/PWA identity is a reviewed, locked brand asset.
# Do NOT run build_assets.py here: that legacy generator recreates the retired
# tilted price-tag/Taka identity and would overwrite the approved S + % mark.
python3 build_catalog.py
python3 build_home.py
python3 build_pages.py
python3 build_trust.py
python3 build_seo.py
python3 build_category.py
python3 audit_all.py
python3 deploy_preflight.py
python3 check_prices.py
python3 stage_deploy.py
python3 release_hardening.py
python3 cache_safe_brand.py

echo 'DONE: full rebuild + audit + hardened staged deployment output (_site)'
