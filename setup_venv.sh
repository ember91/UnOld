#!/bin/bash
set -eEuo pipefail

# Setup python virtual environment
# May need 'pip3 install uv' outside a virtual environment

PYTHON_VERSION="3.12"
top_dir="$(git rev-parse --show-toplevel)"
venv_dir="${top_dir}/.venv"

# Calling 'deactivate' may lead to some problems. Do this instead.
if [[ -f "${top_dir}.venv/bin/deactivate" ]]; then
    "${top_dir}.venv/bin/deactivate"
fi

uv venv --python "/usr/bin/python${PYTHON_VERSION}"

# shellcheck disable=SC2086
# shellcheck source=/dev/null
source "${venv_dir}/bin/activate"
uv pip install -r "${top_dir}/requirements_dev.txt"

# shellcheck disable=SC2086
echo "Remember to run 'source "${venv_dir}/bin/activate"'"
