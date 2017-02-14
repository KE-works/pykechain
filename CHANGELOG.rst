Change Log
==========

pykechain changelog

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
