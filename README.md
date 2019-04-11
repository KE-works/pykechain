# KE-chain Python SDK

[![Version](https://img.shields.io/pypi/v/pykechain.svg)](https://pypi.python.org/pypi/pykechain)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/pykechain.svg)](https://pypi.python.org/pypi/pykechain)
[![Build Status](https://travis-ci.org/KE-works/pykechain.svg?branch=master)](https://travis-ci.org/KE-works/pykechain)
[![Documentation Status](https://readthedocs.org/projects/pykechain/badge/?version=latest)](http://pykechain.readthedocs.io/en/latest/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/github/KE-works/pykechain/badge.svg?branch=master)](https://coveralls.io/github/KE-works/pykechain?branch=master)
[![Updates](https://pyup.io/repos/github/KE-works/pykechain/shield.svg)](https://pyup.io/repos/github/KE-works/pykechain/)
[![Code Quality from Codacy](https://api.codacy.com/project/badge/Grade/d963ed6986b249699ce975cac1bc67f6)](https://www.codacy.com/app/KE-works/pykechain)
[![Join the chat at https://gitter.im/KE-works/pykechain](https://badges.gitter.im/KE-works/pykechain.svg)](https://gitter.im/KE-works/pykechain?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

## About pykechain

`pykechain` is a python library for advanced users and KE-chain configurations to connect and interact fully to all features of [KE-chain](http://www.ke-chain.com), the engineering platform of [KE-works](http://www.ke-works.com). With it you can interact with KE-chain, its product information model (PIM), its workflow information model (WIM) and many other aspects of KE-chain from python scripts or iPython / [Jupyter](http://jupyter.org) notebooks.

It requires normal user access to a KE-chain (version 2) instance for it to work.

## Basic usage

Ensure you have member access to a KE-chain instance and login:

```python
from pykechain import Client
kec = Client(url='https://kec2api.ke-chain.com')
kec.login(username='demo_user', password='pastaplease')
```

Now interact with it:

```python
project = kec.scope('Bike Project')
for part in project.parts():
    print(part.name)
```

## Installation

pykechain is easily installed using pip. pykechain is Python 2.7, 3.4,
3.5, 3.6 and 3.7 compatible:

```bash
pip install pykechain
```
Or if you want to live on the edge, install the latest and greatest from
the master branch:

```bash
pip install https://github.com/KE-works/pykechain/archive/master.zip
```

In scripts you can either use [Pipenv]() or a pip requirements.txt file to install pykechain as a requirement

in a `Pipfile`:
```yaml
[packages]
pykechain = "*"
# or when you want to install a certain branch
pykechain = {ref = "master", git = "https://github.com/KE-works/pykechain"}
```
in a pip `requirements.txt`
```ini
pykechain
# or when you want to install a certain branch i.e. `master`
git+https://github.com/KE-works/pykechain.git@master#egg=pykechain
```

## Changelog

A proper changelog is maintained in the
[Changelog](http://pykechain.readthedocs.io/en/latest/changelog.html)
