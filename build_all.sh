#!/bin/bash
set -e
python3 build_catalog.py && python3 build_assets.py && python3 build_home.py && python3 build_pages.py && python3 build_trust.py && python3 build_seo.py && python3 build_category.py && python3 audit_all.py && python3 deploy_preflight.py
echo 'DONE: full rebuild + audit + launch preflight'
