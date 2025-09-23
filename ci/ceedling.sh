#!/usr/bin/env bash
set -e

PROJECT_ROOT="$(pwd)"
rm -f report.xml
rm -f coverage.lcov
rm -rf coverage_report


if [ $# -eq 0 ]; then
    echo "No test functions specified - running all tests"
    ceedling test:all
else
    echo "Running specific test functions: $@"
    TEST_CASES=""
    for test_func in "$@"; do
        if [ -z "$TEST_CASES" ]; then
            TEST_CASES="$test_func"
        else
            TEST_CASES="$TEST_CASES,$test_func"
        fi
    done
    echo "Ceedling test filter: $TEST_CASES"
    ceedling test:all --test-case="$TEST_CASES"
fi

mv build_test/artifacts/test/junit_tests_report.xml $PROJECT_ROOT/report.xml


rm -rf build_test/artifacts/gcov/*
ceedling gcov:all
mkdir coverage_report
gcovr -r . --html -o $PROJECT_ROOT/coverage_report/index.html
gcovr -r . --lcov -o $PROJECT_ROOT/coverage.lcov


# report to EmbedOps platform
# uncomment the section below once Repo Variable EMBEDOPS_API_REPO_KEY is set.
# If you have access, this key can be found at https://app.embedops.io/app/manage/repos/<Embedops Repo UUID>

if [ "$CI" = "true" ]; then
   # do not fail if error reporting
   set +e
   eo report unittest report.xml
   eo report coverage coverage.lcov
   set -e
fi
