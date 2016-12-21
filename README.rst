KE-chain Python SDK
===================

.. image:: https://travis-ci.org/KE-works/pykechain.svg?branch=master
:target: https://travis-ci.org/KE-works/pykechain
    :alt: Build Status

.. image:: https://readthedocs.org/projects/pykechain/badge/?version=latest
:target: http://pykechain.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

About pykechain
---------------

pykechain is a python library for advanced users and KE-chain configurations to connect and interact fully to all
features of `KE-chain <http://www.ke-chain.com>`, the engineering platform of `KE-works <http://www.ke-works.com>`.
With it you can interact with KE-chain, its product information model (PIM), its workflow information model (WIM) and
many other aspects of KE-chain from python scripts or iPython / `Jupyter <http://jupyter.org>` notebooks.

It requires normal user access to a KE-chain (version 2) instance for it to work.

Very Basic Use
--------------

Ensure you have member access to a KE-chain instance and login

    from pykechain import Client
    kec = Client(url='https://kec2api.ke-chain.com')
    kec.login(username='demo_user', password='pastaplease')

Now interact with it

    project = kec.project.get('Bike')
    for part in project.parts():
        print(part.name)

Installation
------------

pykechain is easily installed using pip. pykechain is Python 2.7 and Python 3.4 compatible

    pip install https://github.com/KE-works/pykechain/archive/master.zip