KE-chain Python SDK
===================

.. image:: https://travis-ci.org/KE-works/pykechain.svg?branch=master
    :target: https://travis-ci.org/KE-works/pykechain
    :alt: Build Status

.. image:: https://readthedocs.org/projects/pykechain/badge/?version=latest
    :target: http://pykechain.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://coveralls.io/repos/github/KE-works/pykechain/badge.svg?branch=master
    :target: https://coveralls.io/github/KE-works/pykechain?branch=master
    :alt: Coverage Status


About pykechain
---------------

pykechain is a python library for advanced users and KE-chain configurations to connect and interact fully to all
features of `KE-chain <http://www.ke-chain.com>`__, the engineering platform of `KE-works <http://www.ke-works.com>`__.
With it you can interact with KE-chain, its product information model (PIM), its workflow information model (WIM) and
many other aspects of KE-chain from python scripts or iPython / `Jupyter <http://jupyter.org>`__ notebooks.

It requires normal user access to a KE-chain (version 2) instance for it to work.

Very Basic Use
--------------

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

pykechain is easily installed using pip. pykechain is Python 2.7 and Python 3.4 compatible::

    pip install pykechain
