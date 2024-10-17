#!/bin/bash
set -eEuo pipefail

top_dir="$(git rev-parse --show-toplevel)"
file_name_base="$(basename "${top_dir}")"

git archive --format zip HEAD >"${top_dir}/${file_name_base}.zip"
