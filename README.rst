KE-chain Python SDK
===================

.. image:: https://img.shields.io/pypi/v/pykechain.svg
    :target: https://pypi.python.org/pypi/pykechain
    :alt: Version

.. image:: https://img.shields.io/pypi/pyversions/pykechain.svg
    :target: https://pypi.python.org/pypi/pykechain
    :alt: Supported Python Versions

.. image:: https://travis-ci.org/KE-works/pykechain.svg?branch=master
    :target: https://travis-ci.org/KE-works/pykechain
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

It requires normal user access to a KE-chain (version 2) instance for it to work.

.. warning::
   This is the **last release** that is compatible with **Python 2.7**, `which is due for sunsetting in Januari 2020 <https://www.python.org/dev/peps/pep-0373/>`_.

   This is the **last release** that is compatible with the **KE-chain 2 API** (KE-chain API versions < 3.0).

.. note::
   For releases of ``KE-chain >= v3.0``, you need a ``pykechain >= 3.0``.


Basic usage
-----------

Ensure you have member access to a KE-chain instance and login::

    from pykechain import Client
    kec = Client(url='https://kec2api.ke-chain.com')
    kec.login(username='demo_user', password='pastaplease')

Now interact with it::

    project = kec.scope('Bike Project')
    for part in project.parts():
        print(part.name)

Installation
------------

pykechain is easily installed using pip. pykechain is Python 2.7, 3.4, 3.5, 3.6 and 3.7 compatible::

    pip install pykechain

Or if you want to live on the edge, install the latest and greatest from the master branch::

    pip install https://github.com/KE-works/pykechain/archive/master.zip

In scripts you can either use [Pipenv]() or a pip requirements.txt file to install pykechain as a requirement

in a `Pipfile`::

    [packages]
    pykechain = "*"
    # or when you want to install a certain branch
    pykechain = {ref = "master", git = "https://github.com/KE-works/pykechain"}

in a pip `requirements.txt`::

    pykechain
    # or when you want to install a certain branch i.e. `master`
    git+https://github.com/KE-works/pykechain.git@master#egg=pykechain

Changelog
---------

A proper changelog is maintained in the `Changelog <http://pykechain.readthedocs.io/en/latest/changelog.html>`__

