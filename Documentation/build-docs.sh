#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

sphinx-build -b html . ./output

if [ "$1" = "--open" ]; then
   xdg-open ./output/index.html
fi
