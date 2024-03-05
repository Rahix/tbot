#!/bin/bash
set -e

if [ "$#" -ne 1 ]; then
    echo "usage: $0 <release>" >&2
    exit 1
fi

newrel="$1"
today="$(date --rfc-3339=date)"

if ! git diff --exit-code HEAD; then
    echo >&2
    echo "$0: Aborted due to uncommitted changes." >&2
    exit 1
fi

# First, update versionadded, etc. directives
# -------------------------------------------
candidates="$(rg --files-with-matches ":: UNRELEASED")"
sed -i "s/:: UNRELEASED/:: $newrel/g" $candidates
git commit -s -m "docs: Update version references" -- $candidates

# Update CHANGELOG.md, __about__.py, and README.md
# ------------------------------------------------
sed -i -f - ./CHANGELOG.md <<EOF
/^## \[Unreleased\]$/a \\
\\
\\
## [$newrel] - $today
s@^\[Unreleased\]: \\(.*\\)/v\\(.*\\)\.\.\.\\(.*\\)\$@\
[Unreleased]: \1/v$newrel...\3\\
[$newrel]: https://github.com/Rahix/tbot/compare/v\2...v$newrel\
@
EOF

# sed -i -f - ./tbot/__about__.py <<EOF
# /^__version__/c \\
# __version__ = "$newrel"
# EOF

sed -i -f - ./README.md <<EOF
s/^\\(pip3 install --user -U .*@\\).*$/\1v$newrel/
EOF

sed -i -f - ./Documentation/installation.rst <<EOF
s/\\(pip3 install -U --user .*@\\).*$/\1v$newrel/
EOF

# git commit -s -m "Prepare $newrel" -- ./CHANGELOG.md ./tbot/__about__.py README.md
git commit -s -m "Prepare $newrel" -- CHANGELOG.md README.md Documentation/installation.rst
git tag -s "v$newrel" -m "Version $newrel"
