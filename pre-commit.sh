#!/bin/bash
set -eEuo pipefail

# See install_git_hooks.sh

nox -t lint test
