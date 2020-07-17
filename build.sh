#/bin/bash

CURRENT_DIR=$(pwd)
PROJECT_DIR=$(dirname $0)

cd $PROJECT_DIR

rm -rf dist/*.tar.gz
rm -rf dist/*.whl
python3 setup.py sdist bdist_wheel
python3 -m pip install --upgrade dist/*.whl

cd $CURRENT_DIR
