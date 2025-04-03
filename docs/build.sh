#!/bin/bash

source_venv() {
  VENV_DIR=$1
  if [[ "$VIRTUAL_ENV" == "" ]]; then
    if [[ ! -d "${VENV_DIR}"/venv ]]; then
      virtualenv "${VENV_DIR}"/venv --python=python3
    fi
    source "${VENV_DIR}"/venv/bin/activate
  else
    echo "Found existing virtualenv"
  fi
}

SCRIPT_DIR=$(dirname "$0")
BUILD_DIR=build_docs
[[ -z "${DOCS_OUTPUT_DIR}" ]] && DOCS_OUTPUT_DIR=generated/docs
[[ -z "${GENERATED_RST_DIR}" ]] && GENERATED_RST_DIR=generated/rst
[[ -z "${GENERATED_AUTOGEN_RST_DIR}" ]] && GENERATED_AUTOGEN_RST_DIR=generated/rst/autogen

rm -rf "${DOCS_OUTPUT_DIR}"
mkdir -p "${DOCS_OUTPUT_DIR}"

rm -rf "${GENERATED_RST_DIR}"
mkdir -p "${GENERATED_RST_DIR}"

source_venv "$BUILD_DIR"
pip3 install -r "${SCRIPT_DIR}"/requirements.txt

rsync -av "${SCRIPT_DIR}"/root/ "${SCRIPT_DIR}"/conf.py "${GENERATED_RST_DIR}"

export EXIT_ON_BAD_CONFIG='false'
set -x
sphinx-build -j auto --keep-going -b html "${GENERATED_RST_DIR}" "${DOCS_OUTPUT_DIR}"
