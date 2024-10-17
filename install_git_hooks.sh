#!/bin/bash
set -eEuo pipefail

top_dir="$(git rev-parse --show-toplevel)"
path_src=pre-commit.sh
path_dst="${top_dir}/.git/hooks/$(basename "${path_src}")"

cp "${path_src}" "${path_dst}"
chmod +x "${path_dst}"
