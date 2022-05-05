KE-chain Python SDK
===================

.. image:: https://img.shields.io/pypi/v/pykechain.svg
    :target: https://pypi.python.org/pypi/pykechain
    :alt: Version

.. image:: https://img.shields.io/pypi/pyversions/pykechain.svg
    :target: https://pypi.python.org/pypi/pykechain
    :alt: Supported Python Versions

.. image:: https://github.com/KE-works/pykechain/workflows/Test%20pykechain/badge.svg?branch=main
    :target: https://github.com/KE-works/pykechain/actions?query=workflow%3A%22Test+pykechain%22+branch%3Amaster
    :alt: Build Status

.. image:: https://readthedocs.org/projects/pykechain/badge/?version=stable
    :target: https://pykechain.readthedocs.io/en/stable/?badge=stable
    :alt: Documentation Status

.. image:: https://coveralls.io/repos/github/KE-works/pykechain/badge.svg?branch=main
    :target: https://coveralls.io/github/KE-works/pykechain?branch=master
    :alt: Coverage Status

.. image:: https://pyup.io/repos/github/KE-works/pykechain/shield.svg
    :target: https://pyup.io/repos/github/KE-works/pykechain/
    :alt: Updates

.. image:: https://app.codacy.com/project/badge/Grade/9584610f1d4d474798c89fe87137c157
    :target: https://www.codacy.com/gh/KE-works/pykechain/dashboard
    :alt: Code Quality from Codacy


About pykechain
---------------

``pykechain`` is a python library for advanced users of KE-chain. It will enable users to connect and fully interact
to all features of `KE-chain <http://www.ke-chain.com>`__, the digital verification and high tech systems design
platform of `KE-works <http://www.ke-works.com>`__.
With it you can interact with KE-chain, its parts, projects, forms, workflows, activities, scripts and all other
aspects of KE-chain from within python scripts or iPython / `Jupyter <http://jupyter.org>`__ notebooks.

It requires a normal user access to a KE-chain (version 3) instance for it to work.

.. note::
   This version of pykechain (> 4.0.0) is compatible with the latest release of KE-chain where we
   added the Forms feature. It is fully backward compatible with all KE-chain versions v2022 and higher.
   This version discontinues support for python version 3.6.

.. note::
   This version of pykechain (> 3.0.0) is suited from KE-chain versions > 3 (or > v2021) running
   on ``python >= 3.7`` exclusively. If you desire to connect to an older version of KE-chain or
   run on ``python 2.7``, please use a ``pykechain v2`` release. Put in the requirements ``pykechain~=2.7``.

Basic usage
-----------

Ensure you have member access to a KE-chain instance and login::

    from pykechain import Client
    kec = Client(url='https://<domain>.ke-chain.com')
    kec.login(username='demo_user', password='pastaplease')

Now interact with it::

    project = kec.scope('Bike Project')
    for part in project.parts():
        print(part.name)

Installation
------------

pykechain is easily installed using pip. ``pykechain`` is Python ``3.7``, ``3.8``, ``3.9``, ``3.10``
and ``pypy3`` compatible::

    pip install pykechain

Or if you want to live on the edge, install the latest and greatest from the master branch::

    pip install https://github.com/KE-works/pykechain/archive/main.zip

In scripts you can either use `Pipenv <https://github.com/pypa/pipenv>`__ or a pip ``requirements.txt`` file to
install ``pykechain`` as a requirement

in a ``Pipfile``::

    [packages]
    pykechain = "*"
    # or when you want to install a certain branch
    pykechain = {ref = "main", git = "https://github.com/KE-works/pykechain"}

in a pip ``requirements.txt``::

    pykechain
    # or when you want to install a certain branch i.e. `main`
    git+https://github.com/KE-works/pykechain.git@main#egg=pykechain

Changelog
---------

A proper changelog is maintained in the `Changelog <http://pykechain.readthedocs.io/en/latest/changelog.html>`__
