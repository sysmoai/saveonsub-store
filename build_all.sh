#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
# One authoritative governed staging build; never runs legacy priced generators.
python3 build_site.py
echo "Governed build complete; NOT DEPLOYED"
