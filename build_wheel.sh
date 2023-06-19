#!/usr/bin/env bash

rm -rf ./build ./dist
python setup.py sdist bdist_wheel --universal
echo "--- uploading to PyPI with either your username or username=__token__ and an API token recorded."
twine upload dist/pykechain-*
