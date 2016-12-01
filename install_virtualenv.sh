#!/bin/bash

ENV=_venv35

virtualenv --python=python3 ${ENV}

source ${ENV}/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

jupyter serverextension enable --py jupyterlab --sys-prefix