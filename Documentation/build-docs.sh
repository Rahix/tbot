#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

sphinx-build -b html . ./output
