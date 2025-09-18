#!/usr/bin/env bash
set -eo pipefail

cd app && west build 2>&1 | tee build.log

# report to EmbedOps platform
# uncomment the section below once Repo Variable EMBEDOPS_API_REPO_KEY is set.
# If you have access, this key can be found at https://app.embedops.io/app/manage/repos/<Embedops Repo UUID>

# if [ "$CI" = "true" ]; then
#    # do not fail if error reporting
#    set +e
#    EMBEDOPS_COMPILER=GCC eo report memusage build.log
#    set -e
# fi