#! /bin/bash
set -eo pipefail
cd "$(git rev-parse --show-toplevel)"

jq -r '.steps[]' ci/pipeline.json | while read script; do
  bash -c "$script"
done