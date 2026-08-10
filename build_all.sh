#!/bin/bash
set -euo pipefail

# SAVEONSUB default build is the strict L1 public-information release.
# Historical commerce generators remain in the repository for migration/audit
# evidence but are not part of the default build or any production path.
python3 validate_authority_boundaries.py
python3 validate_media_registry.py
python3 validate_catalog_model.py
python3 build_public_info_v3.py
python3 harden_public_info_v3.py

if [ -n "${GITHUB_SHA:-${SAVEONSUB_RELEASE_SHA:-${VERCEL_GIT_COMMIT_SHA:-}}}" ]; then
  python3 stamp_release.py
fi

python3 validate_public_info_v3.py
python3 validate_l1_release.py
python3 stage_deploy.py --public-v3

echo 'DONE: strict L1 public-information build + validation + staging'
