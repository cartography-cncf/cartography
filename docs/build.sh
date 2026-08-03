#!/bin/bash

SCRIPT_DIR=$(dirname "$0")
BUILD_DIR=build_docs
[[ -z "${DOCS_OUTPUT_DIR}" ]] && DOCS_OUTPUT_DIR=generated/docs
[[ -z "${GENERATED_RST_DIR}" ]] && GENERATED_RST_DIR=generated/rst
[[ -z "${GENERATED_AUTOGEN_RST_DIR}" ]] && GENERATED_AUTOGEN_RST_DIR=generated/rst/autogen

rm -rf "${DOCS_OUTPUT_DIR}"
mkdir -p "${DOCS_OUTPUT_DIR}"

rm -rf "${GENERATED_RST_DIR}"
mkdir -p "${GENERATED_RST_DIR}"

rsync -av "${SCRIPT_DIR}"/root/ "${SCRIPT_DIR}"/conf.py "${GENERATED_RST_DIR}"

export EXIT_ON_BAD_CONFIG='false'

# Keep the log out of DOCS_OUTPUT_DIR: that directory is published to gh-pages verbatim.
SPHINX_LOG=$(mktemp)
trap 'rm -f "${SPHINX_LOG}"' EXIT

set -x

sphinx-build -j auto --keep-going -b html "${GENERATED_RST_DIR}" "${DOCS_OUTPUT_DIR}" 2>&1 |
    tee "${SPHINX_LOG}"
SPHINX_STATUS="${PIPESTATUS[0]}"
[[ "${SPHINX_STATUS}" -ne 0 ]] && exit "${SPHINX_STATUS}"

# A broken cross-reference renders as a dead link without failing the build, which is how
# 700 of them accumulated unnoticed. Everything else in the current warning baseline is
# pre-existing, so gate on this category alone rather than on -W.
if grep -q 'myst.xref_missing' "${SPHINX_LOG}"; then
    set +x
    echo "ERROR: broken documentation cross-references:" >&2
    grep 'myst.xref_missing' "${SPHINX_LOG}" >&2
    exit 1
fi
