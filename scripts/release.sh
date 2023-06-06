#!/bin/bash

set -e

CURRENT_RELEASE=$(fgrep __version__ setup.py | sed '/^__version__/!d' | sed "s/^__version__\ *=\ *'\([0-9.]\+\)'$/\1/")
NEXT_RELEASE=$1

if [ "${NEXT_RELEASE}" == "" ]; then
    echo Missing next release parameter
    exit 1
fi

echo "Checking JSON files..."
ls *json || true

pip install twine -U

git pull

find . -type f -name "*.py" -exec sed -i "s/^__version__.*$/__version__ = \"${NEXT_RELEASE}\"/g" {} \;
rm -rf dist

# git add -A
# git commit -m "Release ${NEXT_RELEASE}"
python3 setup.py sdist
# keyring --disable # Executed once
twine upload -u dainok dist/*
# git tag ${NEXT_RELEASE}
# git push
# git push origin --tags
