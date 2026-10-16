#!/usr/bin/env bash
set -euo pipefail

DEST_DIR="${1:-/tmp/enterprise-bench-clean}"
DRY_RUN="${2:-false}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=== Enterprise Workbench Downstream Mirror Export ==="
echo "Source:      ${ROOT_DIR}"
echo "Destination: ${DEST_DIR}"
echo "Dry Run:     ${DRY_RUN}"
echo "====================================================="

RSYNC_FLAGS=("-av" "--stats")
if [ "${DRY_RUN}" = "true" ] || [ "${DRY_RUN}" = "--dry-run" ]; then
  RSYNC_FLAGS+=("-n")
fi

rsync "${RSYNC_FLAGS[@]}" \
  --exclude='.git' \
  --exclude='.venv' \
  --exclude='output' \
  --exclude='doc_output' \
  --exclude='clean_workspace' \
  --exclude='raw_source_files' \
  --exclude='work_archive' \
  --exclude='specs/tti_analytics' \
  --exclude='docs/handovers/handover_archive' \
  --exclude='scratch' \
  --exclude='*.local.json' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.DS_Store' \
  --exclude='.pytest_cache' \
  --exclude='.ruff_cache' \
  "${ROOT_DIR}/" \
  "${DEST_DIR}/"

if [ "${DRY_RUN}" != "true" ] && [ "${DRY_RUN}" != "--dry-run" ]; then
  echo ""
  echo "=== Running Post-Export Static PII Gate ==="
  LEAKS=$(grep -rnEI "toyota|tsusho|ttlc" "${DEST_DIR}/specs/" 2>/dev/null || true)
  if [ -n "${LEAKS}" ]; then
    echo "❌ GATE FAILED: Found legacy client tokens in exported specs/:"
    echo "${LEAKS}"
    exit 1
  else
    echo "✅ GATE PASSED: Zero legacy client tokens found in exported specs/."
  fi
fi
