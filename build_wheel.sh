#!/usr/bin/env bash
rm -rf ./build ./dist
python setup.py sdist bdist_wheel --universal
twine upload dist/pykechain-* --repository pykechain
