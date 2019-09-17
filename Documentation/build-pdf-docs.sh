#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

sphinx-build -b latex -t pygments-light . ./output-pdf
make -C ./output-pdf
