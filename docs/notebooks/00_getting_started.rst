###############
Getting Started
###############

.. note::

    The Getting started guide for pykechain notebooks demonstrates the following:

    * ensuring you have installed Python on your (Windows) computer
    * we install the proper virtualenviroment for pykechain and notebooks


As a new Pykechain user that want to interact with the KE-chain API to add that special feature that is not
provided out of the box, we provide a guide to jumpstart working with pykechain on your computer.

Prerequisites
-------------

A computer running **Windows** 7 or later (64-bit)
    This guide is aimed at Windows 7 or later (64-bit). However Pykechain can run just as easy on (if not easier)
    on computers running Linux or MacOS.

A **Python** 3 installation
    Pykechain is optimised for Python 3.6. However other python versions suchs as 2.7 and 3.5 are fully supported as
    well.

    * If you need help installing python on your computer, please refer to: `The official Python documentation`_
    * Ensure that your `python executable is added to the PATH`_, such that you can use it on the commandline effectively.

Access to a **KE-chain 2** installation
    Please ensure that you have access to a KE-chain intance

.. _The official Python documentation: https://www.python.org/downloads/windows/
.. _python executable is added to the PATH: https://superuser.com/questions/143119/how-to-add-python-to-the-windows-path


Step-by-Step Guide
------------------

1. Setup a virtual python environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We create a new directory for this project, eg. 'pyke-bike'. Create that in your documents. In order to install
pykechain and notebooks we will create a virtual environment in this directory and we will do that from the
windows commandline.

.. image:: /_static/new_folder.png
    :width: 660

Hold 'SHIFT' and open the right-mouse-menu on the newly created folder, select 'open Command Window here...'

.. image:: /_static/open_command_window.png
    :width: 200

Ensure that you are inside the right folder we will type the following in the command window::

    # Install the python package virtualenv
    > pip install virtualenv

    # install a virtual environment 'venv'
    > virtualenv --python=C:\Python\python3.exe venv

    # Activate the virtual environment
    > venv\Scripts\activate

We now have a proper virtualenvironment installed and we are going to install pykechain and notebooks in it.

2. Install pykechain and notebooks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Inside the open command terminal from step 1 type the following::

    > pip install pykechain jupyter

    # When installed correctly, start jupyter notebook by typing
    > jupyter notebook

.. note::

    You may want to include handy additional packages that we use a lot to perform datacrunching such as: ``numpy``,
    ``scipy``, ``matplotlib``, ``mpld3``, and ``pandas``.

.. image:: /_static/command_window_with_jupyter_notebook_response.png
    :width: 660

Jupyter notebook will automatically open your browser to the link provided in the command window output.
If not you need to open your browser to the link provided in the command window.

Go ahead and open new notebook (for Python 3) and start using pykechain in your notebook today

Furter Reading
--------------

You may want to review the :doc:`basic_usage` python notebook provided in the documentation.

Sources
-------

* Install python 3.6: https://www.python.org/downloads/windows/
* Make sure python is added to the path variables:  https://superuser.com/questions/143119/how-to-add-python-to-the-windows-path
* Install pip: https://pip.pypa.io/en/stable/installing/#do-i-need-to-install-pip
