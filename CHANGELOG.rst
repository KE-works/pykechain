Change Log
==========

pykechain changelog

1.5.0 (UNRELEASED)
------------------
 * Added ability to edit the part name and description functionality. See the `Part.edit()` method.
 * Added type annotations throughout the code and added mypy to the continuous integration pipeline to ensure high 
   quality of the code provided.
 * Added the ability to use the bulk_update_properties API endpoint for KE-chain releases later then 2.1.0b. No need to
   alter your pykechain code. The implementation of `Part.update()` method is augmented to use this faster method of
   uploading changes to property values. For connections to legacy KE-chain 2 instances, use the switch `bulk=False`.

1.4.0 (17FEB17)
---------------
 * Added functionality to create part models, just as you create part instances.
 * Added functionality to upload files (using filename), python objects (as json) and matplotlib figures as attachments
 * Added functionality to download attachments directly as file or python objects (from json).
 * Improved logic if you request children or siblings that the corresponding category (Model or Instance) is retrieved.
 * Improved continuous integration.
 * Improved documentation

1.3.0 (16FEB17)
---------------

 * Added functionality to support a select list property type from KE-chain in pykechain. Now you can inquire for the
   options and set the list of options (on the model) to choose from. See documentation of `SelectListProperty`_.
 * Added additional keyword arguments to the `Client.parts()` method. This allows access to additional filters on the
   KE-chain REST API.
 * Fixed a bug that shows a warning when importing pykechain without a `.env` file being present. Improved documentation
   of the `Client.from_env()`_ method. Including an example of this .env file.
 * Improved documentation
 * Improved testing (and coverage)
 * Improved introspection of `PartSet`.

.. _SelectListProperty: http://pykechain.readthedocs.io/en/latest/api/models.html#pykechain.models.SelectListProperty
.. _Client.from_env(): http://pykechain.readthedocs.io/en/latest/api/client.html#pykechain.Client.from_env

1.2.0 (14FEB17)
---------------

 * batch updates of properties in a part using a dictionary is now possible using the part `update({'prop_name': val})`
   `Part`_ method.
 * added relational methods on the part like: `Part.parent()`, `Part.children()` and `Part.siblings()`. See
   documentation of `Part`_ for that.
 * improved documentation
 * improved testing
 * improved introspection of objects due to correct representation for debugging
 * version number now available through pykechain.version

.. _Part: http://pykechain.readthedocs.io/en/latest/api/models.html#pykechain.models.Part

1.1.2 (7FEB17)
--------------

 * improved (iterative) part retriever capability with a batch processed request. Will enable to retrieve large datasets
   than normal, that take longer than a standard timeout. Will concatenate the results of the various requests.
   Check out the documentation for the new `limit` and `batch` parameters on the `Client.parts`_ method.
 * improved upload of files and attachments
 * added bucket and limit filters to limit the number of parts retrieved
 * improved testing
 * improved coverage
 * updated dependencies
 * improved documentation

.. _Client.parts: http://pykechain.readthedocs.io/en/latest/api/client.html#pykechain.Client.parts

1.0.0 (3JAN17)
--------------

 * First public release of pykechain
 * ability to create a client to connect to a KE-chain instance
 * ability to retrieve parts and properties within a KE-chain scope (project)
 * ability to retrieve activities with a KE-chain scope
 * ability to upload and download a property value

0.1.0.dev0 - 0.1.1.dev0 (23DEC16)
---------------------------------

 * Initial pre-release of pykechain
 * ability to create a client to connect to a KE-chain instance
 * ability to retrieve parts and properties within a KE-chain scope (project)
 * limited ability to upload and download a property value
