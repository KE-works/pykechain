Change Log
==========

pykechain changelog

1.10.0 (18AUG17)
----------------
 * Ability to edit the status of an `Activity`. Please refer to the `ActivityStatus` enumerations.
 * Ability to sort properties of a `Part` model.
 * Upgraded the requirements of dependent packages for development.
 * Added tests for all new features to get the > 95% coverage
 * Updated the documentation.

1.9.1 (27JUN17)
---------------
 * Improved testing. Notably on the new inspector objects. No functional change only that we want to reach our goal of 95% test coverage! Thanks to @raduiordache (#137)

1.9.0 (23JUN17)
---------------

 * Added a major new feature to create `Customization`s of activities in KE-chain 2 all programmatically and pythonic. We provide building block classes such as `SuperGrid`, `PaginatedGrid`s and `PropertyGrid`s to make your own task customization. All is documented with examples. A `validation()` method is available. (#110)

    >>> my_task = project.activity('my task')
    >>> bike = project.part(name='Bike')
    >>> customization = Customization()  # init customization object for the task
    >>> my_prop_grid = PropertyGrid(part=bike, title=bike.name)  # create a PropertyGrid
    >>> customization.add_component(my_prop_grid)  # add PropertyGrid to the Customization component list
    >>> customization.validate()  # you can validate the customization
    >>> my_task.customize(customization)  # upload/set the Customization. Ensure you have data access set correctly.

 * Updated the way the `Activity.customize()` method works. This method now accepts a `Customization` object or a josn (as a python dict). It uses the `Customization.validate()` method to validate if it conforms to the required json structure before uploading it to KE-chain.
 * Improved test coverage and refactored the HTTP codes to human readable form. (#128)
 * Added the ability to edit the description of property models. This was included in `Part.create_property(... description=...)` (#135)
 * Add `Part.as_dict()` method to retrieve the properties of a part in pykechain as a python dictionary as `{<property_name> : <property_value>}` (#131)
 * Added the ability to optionally update the name of a part together with the value of its properties. See the `Part.update()` method. (#126)
 * Deprecated the `Activity.create_activity()` method in favor of `Activity.create()`. Use the latter. Will warn with a `DeprecationWarning` until removed.


1.8.0 (05JUN17)
---------------
 * Added `Part.instances()` method for models to find their associated instances. (#113) Also added a
   `Part.instance()` method if you for sure that you will get only a single instance back.
 * Added `Activity.subprocess()`, `Activity.siblings()` and `Activity.children()` methods to the `Activity`.
   It eases relative retrieval of other tasks in the task tree. Documentation is included. (#100)
 * added `Activity.activity_type` property to the Activity.
 * added `ActivityType` enumeration. This can be used to check if the `activity_type` of an `Activity` is either
   a Usertask or a Subprocess.
 * Added ability to retrieve an `Activity` based on an id. As this included in the low level `Client` object,
   it can be used almost everywhere to retrieve an activity by its id (or primary key, pk) eg. in the `Scope.activity`.
 * Added ability to add additional keywords to the activities searcher to be able to search by name, pk, container etc.
 * Added a FutureDeprecationWarning to the `Activity.create_activity()` method. This will is replace with the
   `Activity.create()` method. Update your code please!
 * Added a convenience method to retrieve models and instances related to a task at once:
   `Activity.associated_parts()`. Making use of the already provided method in `Activity.parts()`. (#118)
 * Added missing tests for `Activity.parts()` and `Activity.associated_parts()`
 * added tests for all new features.
 * Updated the documentation.


1.7.3 (01JUN17)
---------------
 * Updated documentation for activity startdate and duedate editting using timezone supported datetime objects.
   If a user want to make use of timezone aware datetime the best way to do it is::

    >>> my_tz = pytz.timezone('Europe/Amsterdam')
    >>> start_date = my_tz.localize(datetime(2017,6,1,23,59,0))
    >>> due_date = my_tz.localize(datetime(2017,12,31))
    >>> my_task.edit(start_date = start_date, due_date = due_date)

 * Fixed a bug where a naive due_date and no provided start_date resulted in an error. Keep them bugs comin'!


1.7.2 (01JUN17)
---------------
 * updated `property.part` property that gets the part for its property. For model this did not work as underlying
   only `category=INSTANCES` were retrieved. Thanks to @joost.schut for finding it and reporting.
 * updated requirements for development.


1.7.1 (29MAY17)
---------------
 * Added `Part.multiplicity` property method. Use the `pykechain.enums.Multiplicity` to check the multiplicity of a part
   against the set multiplicities.
 * Updated documentation (a.o. the Basic Usage notebook).


1.7.0 (29MAY17)
---------------
 * Added `ReferencyProperty.choices()` convenience method to provide you the list of parts (instances) that are
   acceptable as a choice for the value of the reference property.
 * Added `Part.proxy_model()` method that will return the model that is used as the basis for the proxied model.
   A proxied model is a linkedcopy of the proxy_model that can have a different name, but follow that exact model
   definition of the proxy_model including its properties and submodel parts. A handy way to create model structures
   in the catalog world and use a multiple of those in the product world. An example is provided in the documentation.
 * Added the `Activity.edit()` method to be able to update the activity name, description, start_date, due_date
   and assignee.
 * Added the ability to customize an activity using the `Activity.customize()` method using a proper inspector NG json.
 * Upgraded package `requests` to the latest version.
 * Updated documentation according to PEP257.
 * Updated requirements for development.


1.6.0 (3MAY17)
--------------
 * Added a `Part.model()` method to retrieve the model from an instance.
 * (Backwards Incompatibile) The task configuration (association) API is updated to the
   latest KE-chain release (release 2.1.0b-sprint119 30MAR17). This affects the `activity.configure()` method.
   This change is not compatible with older KE-chain 2 releases. For older KE-chain 2 releases use a
   pykechain version < 1.6
 * Added `Getting Started`_ documentation page for pykechain using jupyter notebooks
 * Documentation update for the reference property
 * Updated documentation according to PEP257

.. _Getting Started: http://pykechain.readthedocs.io/en/latest/notebooks/00_getting_started.html

1.5.1 (6APR17)
--------------
 * Patch release to include the python package typing.

1.5.0 (6APR17)
--------------

 * Added ability to edit the part name and description functionality. See the `Part.edit()` method.
 * Added the ability to use the bulk_update_properties API endpoint for KE-chain releases later then 2.1.0b. No need to
   alter your pykechain code. The implementation of `Part.update()` method is augmented to use this faster method of
   uploading changes to property values. For connections to legacy KE-chain 2 instances, use the switch `bulk=False`.
 * Added the ability to create a new part and provide its properties values for KE-chain releases later then 2.1.0b.
   You can use the new `Part.add_with_properties()` method and it will connect to the new KE-chain API endpoint of
   'new_instance_with_properties'. Properties are provided by name and value in a dict. For examples see the docs.
 * Reference properties can now be set with a Part directly. Setting a reference property to None will clear the value.
 * Added the ability to create a proxy model with `Part.add_proxy_to()` and `Client.create_proxy_model()`. For exmaples
   see the documentation.
 * Added enumerations for `Category` and `Multiplicity` in `pykechain.enums`. You can use these constants to ensure
   that these values are correct, aligned and thusfor accepted by KE-chain. Examples are included in the documentation.
 * Attachment properties have now a value set if there is a file attached in KE-chain. Otherwise the value is None.
   Now you are able to check if there is a file attachment set before you download or upload. See the docs for examples.
 * Added type annotations throughout the code and added mypy to the continuous integration pipeline to ensure high
   quality of the code provided.
 * Improved the documentation



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
