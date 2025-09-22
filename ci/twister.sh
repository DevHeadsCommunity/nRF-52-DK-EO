#!/usr/bin/env bash
set -e

PROJECT_ROOT="$(pwd)"
rm -f report.xml
rm -f coverage.lcov
rm -rf coverage_report

echo "[TWISTER] Running tests"
cd $PROJECT_ROOT/app

west twister -T tests/