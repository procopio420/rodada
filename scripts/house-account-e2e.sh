#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../apps/api"
python -m pytest tests/test_house_account_e2e.py "$@"
