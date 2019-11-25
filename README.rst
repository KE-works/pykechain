KE-chain Python SDK
===================

.. image:: https://img.shields.io/pypi/v/pykechain.svg
    :target: https://pypi.python.org/pypi/pykechain
    :alt: Version

.. image:: https://img.shields.io/pypi/pyversions/pykechain.svg
    :target: https://pypi.python.org/pypi/pykechain
    :alt: Supported Python Versions

.. image:: https://github.com/KE-works/pykechain/workflows/Test%20pykechain/badge.svg?branch=master
    :target: https://github.com/KE-works/pykechain/actions?query=workflow%3A%22Test+pykechain%22+branch%3Amaster
    :alt: Build Status

.. image:: https://readthedocs.org/projects/pykechain/badge/?version=latest
    :target: http://pykechain.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://coveralls.io/repos/github/KE-works/pykechain/badge.svg?branch=master
    :target: https://coveralls.io/github/KE-works/pykechain?branch=master
    :alt: Coverage Status

.. image:: https://pyup.io/repos/github/KE-works/pykechain/shield.svg
    :target: https://pyup.io/repos/github/KE-works/pykechain/
    :alt: Updates

.. image:: https://api.codacy.com/project/badge/Grade/d963ed6986b249699ce975cac1bc67f6
    :target: https://www.codacy.com/app/KE-works/pykechain
    :alt: Code Quality from Codacy

.. image:: https://badges.gitter.im/KE-works/pykechain.svg
   :alt: Join the chat at https://gitter.im/KE-works/pykechain
   :target: https://gitter.im/KE-works/pykechain?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge

About pykechain
---------------

pykechain is a python library for advanced users and KE-chain configurations to connect and interact fully to all
features of `KE-chain <http://www.ke-chain.com>`__, the engineering platform of `KE-works <http://www.ke-works.com>`__.
With it you can interact with KE-chain, its product information model (PIM), its workflow information model (WIM) and
many other aspects of KE-chain from python scripts or iPython / `Jupyter <http://jupyter.org>`__ notebooks.

It requires normal user access to a KE-chain (version 3) instance for it to work.

.. note::
   This version of pykechain (> 3.0.0) is suited from KE-chain versions > 3 running on ``python >= 3.5`` exclusively.
   If you desire to connect to an older version of KE-chain or run on ``python 2.7``, please use a `pykechain v2`
   release.

Basic usage
-----------

Ensure you have member access to a KE-chain instance and login::

    from pykechain import Client
    kec = Client(url='https://kec3api.ke-chain.com')
    kec.login(username='demo_user', password='pastaplease')

Now interact with it::

    project = kec.scope('Bike Project')
    for part in project.parts():
        print(part.name)

Installation
------------

pykechain is easily installed using pip. pykechain is Python ``3.5``, ``3.6``, ``3.7``, ``3.8`` and ``pypy3`` compatible::

    pip install pykechain

Or if you want to live on the edge, install the latest and greatest from the master branch::

    pip install https://github.com/KE-works/pykechain/archive/master.zip

In scripts you can either use [Pipenv]() or a pip requirements.txt file to install pykechain as a requirement

in a ``Pipfile``::

    [packages]
    pykechain = "*"
    # or when you want to install a certain branch
    pykechain = {ref = "master", git = "https://github.com/KE-works/pykechain"}

in a pip ``requirements.txt``::

    pykechain
    # or when you want to install a certain branch i.e. `master`
    git+https://github.com/KE-works/pykechain.git@master#egg=pykechain

Changelog
---------

A proper changelog is maintained in the `Changelog <http://pykechain.readthedocs.io/en/latest/changelog.html>`__
