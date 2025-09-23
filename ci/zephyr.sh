#!/usr/bin/env bash
set -e

git config --global --add safe.directory "$(pwd)"

west update --name-cache $HOME/.embedops/cache/name && pip install -q -r zephyr/scripts/requirements.txt
cd app && west build -p always 2>&1 | tee build.log

# EMBEDOPS_COMPILER=GCC eo report memusage build.log
