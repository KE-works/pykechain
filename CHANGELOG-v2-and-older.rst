Change Log
==========

This changelog file holds the changed smaller than version 3.0.0.

2.7.0 (31OKT19)
---------------

.. warning::
   This is the **last release** that is compatible with **Python 2.7**, `which is due for sunsetting in Januari 2020 <https://www.python.org/dev/peps/pep-0373/>`_.

   This is the **last release** that is compatible with the **KE-chain 2 API** (KE-chain API versions < 3.0).

.. note::
   For releases of ``KE-chain >= v3.0``, you need a ``pykechain >= 3.0``.

 * Added a function to retrieve the associated activities of a part: `Part.associated_activities()` and `Property.associated_activities()`. (#503 - Thanks to @raduiordache for the PR)
 * Added a function to count parts `Part.count_instances()` using a lightweight call to the API. (#485 - Thanks to @raduiordache for the PR)
 * Updated dependent versions for development: pytest (5.2.2),tox (3.14.0), twine (2.0.0), matplotlib (3.1.1), Sphinx (2.2.1), semver (2.9.0), flake8 (3.7.9), mypy (0.740), jsonschema (3.1.1), nbsphinx (0.4.3), pydocstyle (4.0.1)
 * Added a source distribution to PyPI.

2.6.1 (17JUN19)
---------------
 * Fixed a bug where in the move/copy functionality the options to `ReferenceProperty` and `AttachmentProperty` where not passed down. Thanks to @raduiordache. (#502)
 * Updated dependent versions for development: requests (2.22.0), pytest (4.6.3),tox (3.12.1), twine (1.13.0), matplotlib (3.1.0), Sphinx (2.1.1).

2.6.0 (23APR19)
---------------
 * Added the possibility to create a scope, clone a scope, and delete a scope. Check `Client.create_scope()`, `Scope.clone` and `Scope.delete` for documentation. (#359)

2.5.7 (18APR19)
---------------
 * Added additional properties for the `Service` and `ServiceExecution` class. Now you can retrieve the `Service.filename` amoungst others. Please refer to the documentation of `Service` and `ServiceExecution` to see the properties that are now available (a feature request by @JelleBoersma). #480
 * We added a utility function to `parse_datetime` strings into `datetime` objects. These strings are in a json response from the KE-chain backend and are now properly translated and timezoned. #482
 *  Updated dependent versions for development: pytest (4.4.1), mypy (0.701), tox (3.9.0).

2.5.6 (13APR19)
---------------
 * Small patch release to ensure that the `Activity2.assignees` returns an empty list when nobody is assigned to the task. #477. Thanks to @raduiordache for finding it out.

2.5.5 (11APR19)
---------------
 * Added properties to the `Property` to directly access properties such as `unit`, `description` and `type`. `Property.type` refers to a `PropertyType` enum. #469
 * Added a property to the `AttachmentProperty.filename` to return the filename of an attachment. #472
 * Added a property to retrieve the assignees list of an activity through `Activity2.assignees`. This will return a list of `User`'s assigned to the activity. #473
 * Added additional properties to `Service` such as `name`, `description` and `version` of a service. #469
 * Added additional properties to `Scope` such as `description`, `status` and `type`. #469
 * Updated dependent versions for development: matplotlib (3.0.3), jsonschema (3.0.1), pytest (4.4.0), sphinx (2.0.1), mypy (0.700), tox (3.8.6).

2.5.4 (28FEB19)
---------------
 * Fixed a bug where the update of the single select list options could overwrite the existing validators. Thanks to @jelleboersma for finding this out and creating the PR. (#446)
 * Updated dependent versions for development: sphinx (1.8.4), mypy (0.670), pytest (4.3.0), flake8 (3.7.7), jsonschema (3.0.0), pyOpenSSL (for python 2.7, 19.0.0).
 * Updated security advisory to install requests package later than 2.20.0 (CVE-2018-18074).

2.5.3 (21JAN19)
---------------
 * Fixed a bug where a numeric range validator from a property was not correctly instantiated for provided min/max values when the validator was retrieved from the KE-chain backend. Thanks to @bastiaanbeijer for finding this! (#435)
 * Updated dependent versions for development: requests (2.21.0), sphinx (1.8.3), pytest (4.1.1), mypy (0.660), nbsphinx (0.4.2), tox (3.7.0).


2.5.2 (30NOV18)
---------------
 * Fixed the customizations to be compatible with KE-chain 3: `Custom Title` replaced by `Custom title`; added the possibility to include the `Clone button` where applicable. The `metaWidget` now uses 'Set height' and 'Automatic height'. (#421) thanks to @raduiordache.
 * Updated dependent versions for development: requests (2.20.1), sphinx (1.8.2), pytest (4.0.1), requests (2.20.0), matplotlib (3.0.2)

2.5.1 (05NOV18)
---------------
 * patch release to include the dependency pytz in the normal list of dependencies, not only for development.

2.5.0 (1NOV18)
--------------
 * Added the ability to set and retrieve the scope tags using the `Scope.tags` property. (#367)
 * Added timezone, language and email to the user object. You can access this directly as a property on the `User` object. (#378)
 * Ensured that you can now filter users on their name, username and email. (#373)
 * Added the possibility to generate a PDF from an activity even with attachments included. The later is an async process on the KE-chain server and pykechain uses a 'hint' to retrieve the PDF once it becomes available on the server. It has an timeout of 100 seconds. (#406)
 * included many updated tests for the copy_move functionality including cross reference properties. (#376)
 * Updated dependent versions for development: semver (2.8.1), pydocstyle (3.0.0), mypy (0.641), requests (2.20.0), flake8 (3.6.0), matplotlib (3.0.1), pytest (3.9.3), tox (3.5.3)

2.4.1 (26SEP18)
---------------
 * Added support for the `Scope.team` property. Will return a `Team` object if the project has a team associated to it, otherwise None. (#392)
 * Included `Team` object in the API documentation.

2.4.0 (26SEP18)
---------------
 * Added the `Team` concept. You can now query the API to retrieve `Teams` using `client.team(name='My own team')`. You can also now `Team.add_members` and `Team.remove_members` with their `TeamRoles`. (#391)
 * Updated dependent versions for development: twine (1.12.1)

2.3.3 (24SEP18)
---------------
 * Fixed an issue with the `scope.edit()` method. It will handle now the assignment of the team with a `team_id` correctly. Thanks @stefan.vanderelst (#388)
 * Updated dependent versions for development: tox (3.4.0), pytest (3.8.1), sphinx (1.8.1)

2.3.2 (19SEP18)
---------------
 * The setting of the min and max value of the numeric range validator could not correctly deal with a value of None. That is fixed. Thanks to @JelleBoersma for the fix! (#382)
 * Additional widgets are introduced in KE-chain or in the process of being introduced, so we updated the enumerations. In this process we also updated the jsonschema of the widget to check against before uploading a customization to KE-chain (#369)
 * Updated dependent versions for development: tox (3.2.1), pytest (3.8.0), nbsphinx (0.3.5), sphinx (1.8.0), mypy (0.630) and matplotlib (3.0.0)

2.3.1 (2AUG18)
--------------
 * The details of a scope can now be edited using `Scope.edit()` method. This contains action already prepared for the KE-chain 2.16.0-143 release (Mid August). (#357)

    For example:

     >>> from datetime import datetime
     >>> project.edit(name='New project name',description='Changing the description just because I can',start_date=datetime.utcnow(),status=ScopeStatus.CLOSED)

  * Updated dependent versions for development: pytest (3.7.0)

    For example:

     >>> from datetime import datetime
     >>> project.edit(name='New project name',description='Changing the description just because I can',start_date=datetime.utcnow(),status=ScopeStatus.CLOSED)

  * Updated dependent versions for development: pytest (3.7.0)

    For example:

     >>> from datetime import datetime
     >>> project.edit(name='New project name',description='Changing the description just because I can',start_date=datetime.utcnow(),status=ScopeStatus.CLOSED)

  * Updated dependent versions for development: pytest (3.7.0)

    For example:

     >>> from datetime import datetime
     >>> project.edit(name='New project name',description='Changing the description just because I can',start_date=datetime.utcnow(),status=ScopeStatus.CLOSED)

  * Updated dependent versions for development: pytest (3.7.0)

   For example:

    >>> from datetime import datetime
    >>> project.edit(name='New project name',
    ...              description='Changing the description just because I can',
    ...              start_date=datetime.utcnow(),  # naive time is interpreted as UTC time
    ...              status=ScopeStatus.CLOSED)

 * Updated dependent versions for development: pytest (3.7.0)

2.3.0 (26JUl18)
---------------
 * We added additional utilities to help pykechain script developers to `Part.copy()`, `Part.move()` and `Part.clone()` part models and part instances. (#343)

For example; To move part models, their children (subtree) and their instances:

    >>> model_to_move = project.model(name='Model to be moved')
    >>> bike = project.model('Bike')
    >>> model_moved = model_to_move.move(target_parent=bike, name='Moved model',
    >>>                                  include_children=True,
    >>>                                  include_instances=True)

 * We added show headers and show columns in the arguments of the property grid to align to KE-chain functionality of the widget. (#350)
 * We added the posibility to use a JSON widget to the list of allowed widgets. (#351)
 * We added the posibility to update the options of a reference property. (#352)
 * Updated dependent versions for development: pytest (3.6.3), tox (3.1.2), sphinx (1.7.6), mypy (0.620)

2.2.4 (22JUN18)
---------------
 * An issue was fixed where the `suppress_kevents` flag was not correctly injected in the API request for all functions that created parts. (#340)
 * Changed the way the cached children are stored when the `Part.children()` method is used. It is now cached as a `List` instead of a `Partset` and you can iterate over the `List` many times in your application. Thanks to Jelle Boersma for finding this. (#341)
 * Updated dependent versions for development: pytest (3.6.2), mypy (0.610), requests (2.19.1)

2.2.3 (5JUN18)
--------------
 * An issue was fixed in the `Activity2.siblings()` function. It now returns the actual siblings (other children of the common parent (subprocess)) for WIM2 based Activities. Thanks to @bastiaanbeijer for finding it, thanks to @raduiordache for fixing it. (#332)
 * Updated dependent versions for development: pytest (3.6.1), semver (2.8.0), pyopenssl (18.0.0), sphinx (1.7.5)

2.2.2 (27MAY18)
---------------
 * We fixed an issue with the pdf download option to ensure that the attachements property is passed as well in preparation for the async pdf downloader release in KE-chain 2.13.0-140 (#329). Found and fixed by @raduiordache; thanks!

2.2.1 (23MAY18)
---------------
 * We ensured that old pykechain code to create a property model when not using the `PropertyType` enums is still compatible with changes introduced in version 1.16.0 (MAR18). We improved the documentation for `Client.create_property()` and `enums.PropertyTypes`. Using 'CHAR' (pre 1.16 style) instead of 'CHAR_VALUE' (enum style) will result in a warning (with suggestion to change this) for old code and will be corrected. Using an invalid `property_type` will result in an `IllegalArgumentError`. (#326)

2.2.0 (14MAY18)
---------------

Major feature: Property validators
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 * We added support for validators to KE-chain v2.12.0-139 and pykechain. Validators objects are stored on a property and can be used to validate the value of a property. The validator objects are also visualised in the KE-chain frontend. (#317)

Validators have a representation in the frontend of KE-chain 2 (see also documentation on: https://support.ke-chain.com/). The validators are stored on the `Property` object and currently the following validators are implemented:

 * :class:`NumericRangeValidator`: When you provide a range, the validate can check if the value of the property is within range. It can even check a stepsize. See the documentation for :class:`NumericRangeValidators`. A representation in KE-chain is available when the value does not conform to this range.
 * :class:`RequiredFieldValidator`: When you add this to a property (model), the property validates when a value is provided. There is a representation in KE-chain frontend available.
 * :class:`RegexStringValidator`: A special validation to check a string (eg textfield) against a regex pattern. There *no representation in KE-chain 2 in version v2.12.0-138*.
 * :class:`OddNumberValidator` and :class:`EvenNumberValidator`: a validator that checks a numeric field (decimal or integer field) if it is an even or odd number. There *no representation in KE-chain 2 in version v2.12.0-138*.
 * :class:`SingleReferenceValidator`: a special validator that ensures that there can only be a single referenced part selected in a (multi) reference property.

To validate the property object there are several new functions available. :meth:`Property.validate()` to validate all validators attached to the property using the :attr:`Property.value` as basis for the validation. You will be provided back a resulting list with all validations including their validation reason.

To only check if the Property and its value conforms to the list of Validators, use the :attr:`Property.is_valid` and :attr:`Property.is_invalid` properties.

To retrieve the :class:`PropertyValidator` objects that are stored on the `Property` use the property :meth:`Property.validators`. You can set a list of :class:`PropertyValidator` objects to this property as well, which will be stored on the `Property` in KE-chain using an API call.

To add validators to a property (model)::

    >>> bike_model = project.model(name='Bike')  # type: Part
    >>> electric_range = bike_model.property('electric_range')  # type: Property
    >>> range = NumericRangeValidator(minvalue=0, maxvalue=100)  # instantiate a range validation between 0 and 100
    >>> reqd = RequiredFieldValidator()  # instantiate a requiredFieldValidator
    >>> electric_range.validators = [range, reqd]  # save the validators on the property to KE-chain

To validate a value against a validator::

    >>> bike = project.part(name='Bike')  # type: Part
    >>> electric_range = bike.property('electric_range')  # type: Property
    >>> electric_range.value
    None
    >>> electric_range.is_valid  # No value set, invalid according to the requiredFieldValidator
    False
    >>> electric_range.value = 50
    >>> electric_range.is_valid  # Value is provided AND value is within the range (0, 100)
    True
    >>> electric_range.value = -1
    >>> electric_range.is_valid  # However, the value itself is invalid according to the range validation
    False
    >>> electric_range.validate(reason=True)  # use the explicit validation
    [(False, "Value '-1' should be between 0 and 100"), (True, "Value is provided")]


For more documentation of Validators, please refer to the API documentation at: http://pykechain.readthedocs.io/en/latest/developer_api.html

Fixes and improvements
~~~~~~~~~~~~~~~~~~~~~~
 * A fix was made for the the `Part.populate_descendants()` to be working for part of category `MODEL` too. Thanks to a fix of @raduiordache. (#320)


2.1.1 (10APR18)
---------------
 * We fixed an issue with the caching of the children of a `Part` when you retrieve children with additional filters on it. (#312)

2.1.0 (6APR18)
--------------
 * We added an optimisation to the `Part`. When you use the `Part.children()` method, the children are cached for later re-retrieval. In order to boost performance even more, you can use the `Part.populate_descendants()` function to pre-populate all children for the whole subparttree inside the `Part`. You can easily then access its children without further expensive API calls. (#306)
 * We brought the capabilities of the Text Widget up to specification with the KE-chain 2.10 release. We can now also provide and set the collapsed initial state of the text widget (#310). Thanks to @raduiordache.
 * We added a function to download an activity as PDF (#286). Thanks to @raduiordache.
 * Updated dependent versions for development: pytest (3.5.0), mypy (0.580), nbsphinx (0.3.2), tox (3.0.0), matplotlib (2.2.2), twine (1.11.0), shpinx (1.7.2)

2.0.0 (14MAR18)
---------------

This is a major release of pykechain, adding support for the legacy version of the Workflow Information Module (WIM) in KE-chain as well as the new version WIM2. Based on the version number of the WIM, either an `Activity` or an `Activity2` class is provided.

Major differences
~~~~~~~~~~~~~~~~~

The main diferences in the concepts between WIM1 `Activity` and WIM2 `Activity2` are:

 * In WIM1: The root object is not an `Activity`, while in WIM2 the root object is an `Activity2`. Use predicates such as `is_root` to check this.
 * In WIM1, an `Activity` that exist of the rootlevel, returns a `NotFoundError` when you search for its parent (using the `subprocess()` or `parent` method). In WIM2 you will get the root object back. Use the predicate `is_rootlevel` to help you assess if the `Activity` is indeed on the root level of the project.
 * In WIM1, the types of activity are actually called a `activity_class`, while in WIM2 this is called an `activity_type`. A `UserTask` in WIM1 is a `TASK` in WIM2, and a `Subprocess` in WIM1 is a `PROCESS` in WIM2. The `enums.ActivityTypes` are updated accordingly.
 * In WIM1, the assignees where to be assigned using usernames, in WIM2 user_ids need to be provided. For the sake of compatibility pykechain helps you in this. You can provide usernames to a `Activity2.edit()` and it is automatically translated in user_ids with additional calls to KE-chain.

Other changes
~~~~~~~~~~~~~

 * Revamped the activity API endpoints and functionality to work with the new WIM2 implementation of KE-chain 2.10 (MAR18)
 * Added a number of predicated on the `Activity` object to simplify the introspection of the Activity, eg. `is_rootlevel`, `is_root`, `is_workflow`...
 * We added a translation layer that automatically detects if you connect to WIM1 or WIM2 and automagically translates `activity_class` and `activity_type` and the assigneesids (in lieu of usernames).
 * Added the `Actvity2.parent()` function to retrieve the parent (in lieu for `subprocess()`)
 * Added `User` object in pykechain to check the users in a KE-chain instance.
 * KE-chain for WIM2 added also a version endpoint to check the version of the individual KE-chain 'apps' such as WIM. It is used to automatically give you back the Activity class based on the version you are using. You can check out the `client.app_versions` property.
 * Fixed the way you limit the scope search in Scope.activities() and Scope.activity()

Backward incompatible changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 * Deprecated the 'inspector components' including its base classes.
 * Deprecated the 'single reference property', which is replaced by the `MultiReference` property.

Pending Deprecation Warnings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 * In May 2018 we will deprecate the support of WIM1 in pykechain. `PendingDeprecationWarnings` are in place when you use WIM1 `Activity`.

1.16.0 (14MAR18)
------------------
This is the last release in preparation for the WIM2 release of KE-chain and consequently pykechain. In the next version of pykechain, some backward incompatible changes will happen. A migration path is provided as well.

 * Implemented new functions for adding the following widgets: `Basic table`, `Paginated table`, `JSON`, `Script`, `Notebook`, `Text`, `Attachment viewer` and `Navigation Bar`. (#280)
 * Added two new enums (`SortTable` and `NavigationBarAlignment`) which can be used when adding new widgets. (#280)
 * Added additional enums `WidgetNames` for the proper names of the widgets in the customisation dialog in KE-chain. (#280)
 * Updated the documentation regarding Property Types. (#280)
 * Fixed the enums so they now work correctly for each `PropertyType`. (#280)
 * Wrote a test that tests each property type (we didn't have this before). This will increase the test coverage to ~95% for KE-chain. (#280)
 * Added a new function called `Client.property()`, which allows the user to retrieve one property. (#296)
 * Improved the overall test coverage for `ExtCustomization` class to 100%.
 * increased the coverage of `MultiReference` property tests to 100%. (#296)
 * increased the coverage of `SelectListProperty` tests to 100%. (#296)
 * setting the value of a `SelectListProperty` instance to None empties it.
 * increased the coverage of `Scope` tests to 100%. (#296)
 * increased the coverage of `Client` tests to 99%. (#296)
 * increased the coverage of `Service` tests to 90%. (#296)
 * Updated dependent versions for development: betamax (0.8.1), twine (1.10.0), matplotlib (2.2.0), pytest (3.4.2), mypy (0.570), sphinx (1.7.1)


1.15.4 (15FEB18)
----------------
 * Fixed an issues where the `MultiReference` property did not provide the correct choices. Also fixed a bug where the setting of the value is now performed more robust. (#282)

1.15.3 (8FEB18)
---------------
 * Fixed a bug where the `MultiReference` property only provided back the 'last' `Part` in the internal value due to the way a library parses a list. Fixed that and added tests (#276). Thanks again to @raduiordache.

1.15.2 (5FEB18)
---------------
 * Fixed a bug where the `MultiReference` property could not retrieve parts through the API based on the value of the `MultiReference` property as it incorrectly retrieved the 'id' from the value list (#274). Thanks to @raduiordache!

1.15.1 (2FEB18)
---------------
 * The `Part.property()` method was slightly changed in 1.15 (the argument name was `name` and became `name_or_id`). This is reverted to `name` to be compatible with older pykechain releases. (#271)
 * Updated dependent versions for development: pytest (3.4.0)

1.15.0 (25JAN18)
----------------
 * added ability to provide additional `keyword=value` arguments to many of the part and property methods that either create parts or update properties (#260). This facilitates the use of `suppress_kevents=True` that you might want to use for a backend performance boost. This is a trade-off that the frontend will not be informed of any property updates or new parts until after a reload of the page in the KE-chain frontend application. When you *can use* `suppress_kevents=True` in the method, it is documented in the function. This can be found in de `Developer API docs <http://pykechain.readthedocs.io/en/latest/developer_api.html>`_. Examples of functions that can handle the `supress_kevents=True` as additional `keyword=value` argument are: `Client.create_part()`, `Client.create_model()`, `Part.add()`, `Part.update()`, `Part.edit()` and more like these.
 * added validation of a single select list. The value is not set when it is not in the list of options (#259).
 * enabled to use of property model UUID in the `Part.add_with_properties()` next to using property names. (#258)
 * enabled to search for properties using UUID next to using property names. This is provided for you in `Part.property()`.
 * The `Part.update()` is now considerate if you provide the property UUIDs inside the `update_dict` as well as property names. You can even mix UUIDs and property names together. (#263) Thanks to @raduiordache.
 * functions and methods that check if the correct type was provided to the method as arguments that raised `TypeError` before, are now raising `IllegalArgumentError`.
 * The `Activity.customize()` method and the `InspectorComponents` are now deprecated (since Nov 17) and will raise deprecation errors when called. Use `Activity.customization()` to retrieve the new activity Customization objects.
 * updated dependent versions for development: pytest (3.3.2), sphinx (1.6.6), nbsphinx (0.3.1), matplotlib (2.1.2), mypy (0.560)
 * updated documentation with additional crosslinks and better references.
 * added source code to all API documentation

1.14.0 (11DEC17)
----------------
 * In preparation for the release of KE-chain 2.7.0-132, we added support for multireference properties in pykechain. Pykechain 1.14 is compatible with both older versions of KE-chain as well as the ones supporting multireference properties. The main difference is that you need to provide a list of `Part`s or `part_id`s instead of a single `Part` or `part_id`. It will override the value in KE-chain fully, no adding or substraction methods are provided, you need to do that in your own code.
 * Updated documentation for the `MultiReferenceProperty`.
 * updated dependent versions for development: pytest (3.3.1)

1.13.3 (5DEC17)
---------------
 * added the 'type' attribute to a property (#248)
 * updated the enums documentation to include all the possible enums available (#247)

1.13.2 (4DEC17)
---------------
 * A wrong statuscode check prevented the upload of a script to complete fully in pykechain. The script is properly uploaded, but pykechain checked against wrong code (#246).
 * updated dependent versions for development: pyopenssl (17.5.0), pytest (3.3.0), nbsphinx (0.2.18)

1.13.1 (16NOV17)
----------------
 * Added additional xtypes to the list of allowed xtypes in the customizations in order to support our new widgets. (#240)
 * updated dependent versions for development: pytest (3.2.5)

1.13 (9NOV17)
-------------
 * Added `Service` and `ServiceExecution` models to pykechain (#231). This includes the ability to `create`, `retrieve`, `edit`, `destroy` and `upload` kecpkg files to KE-chain. Also the `retrieve`, `terminate`, and `download log` results for `ServiceExecution`s (which are associated to `Service`s) are available. This brings `pykechain` in line with the full abilities in KE-chain 2 SIM release (31OKT17) (SIM module license needed). Also see the PyPI package `kecpkg-tools` from KE-works to help you smoothen the workflow of creating custom KE-chain supported python packages (`kecpkg`) that can be executed by the KE-chain SIM module.
 * Added additional keywords arguments in the scope and activity searchers. You can now craft complex search queries to the KE-chain API (#231)
 * Prevented the creation of Activities with incorrect activity_class. This is now prevented in pykechain (#225)
 * Added an option for all models to `reload` (will return a new object) and `refresh` (will update in place). (#232)
 * Added additional tests and improved documentation for `Service` and `ServiceExecution` models.
 * updated dependent versions for development: matplotlib (2.1.0), nbsphinx (0.2.16), flake8 (3.5.0), sphinx (1.6.5), mypy (0.540), pydocstyle (2.1.1)

1.12.9 (5OCT17)
---------------
 * Improved scope control for activity queries. Will ensure that the scope_id of an acitivity is properly retrieved and checked for in case of subqueries such as `Activity.children()`, `siblings`, `subprocess`.
 * Updated dependent versions for development: pytest updated to 3.2.3 (#215)

1.12.8 (2OCT17)
---------------
 * Fixed a bug where the scope object was ambigously retrieved during the edit assignees of an activity action. It failed when the scope was closed. Thanks to @raduiordache for its find! (#211)
 * Updated dependent versions for development for tox to 2.9.1 and Sphinx to 1.6.4 (#198, #209)

1.12.7 (2OCT17)
---------------
 * Fixed a bug where a model without an instance raises an incorrect Error. Now it will raise a `NotFoundError` (#207).

1.12.6 (28SEP17)
----------------
 * Fixed a bug in the `models.customisation`. After a succesfull save of a customisation to an activity, the activity could not be retrieved from KE-chain if the activity was part of a closed scope (#205).

1.12.5 (28SEP17)
----------------
 * The `get_project()` helper method will now retrieve a scope a status other than 'ACTIVE' only (#203).
 * Updated the documentation to fix wrongly formatted examples.

1.12.4 (26SEP17)
----------------
 * Fixed a bug in the customization code by which the activity was incorrectly updated after a correctly saved customization to the KE-chain server. In some cases the incorrect customisation was retrieved on name basis, which may resulted in an error raised. Thanks to @raduiordache for finding it (#200).
 * Added `**kwargs` to the `Part.children()`, `Part.siblings()`, `Part.instances()`, `Activity.children()`, and `Activity.siblings()` methods. This will enable more comprehensive searches, eg. by the name of children using `Activity.children(name='Some childs name')` (#199).

1.12.3 (21SEP17)
----------------
 * Fixing the warning: 'could not any envfile' from envparse. Which is suppressed for cosmetics. It is advised to provide a pathname for the envfile when you want to load the environment variables from an envfile (#195).
 * Fixed tests for the envparse warning and refactored the tests to better deal with in-test settings of the environment.

1.12.2 (15SEP17)
----------------
 * Removed a logical error in the checking of the existing of the environment variables.

1.12.1 (15SEP17)
----------------
 * Added the ability to enforce the use of environment variables when the KECHAIN_FORCE_ENV_USE is set to a true value in the environment. Altered documentation and altered tests for that (#193).

1.12 (14SEP17)
--------------
 * Added a new helper `get_project()` to bootstrap a pykechain client and return a project (aka Scope) immediately. You can retrieve a project using direct arguments `url`, `token` (or `username` and `password`), and `scope_id` (or `scope` name). Alternatively, you can provide an `.env` file or provide the arguments from the environment as the environment variables `KECHAIN_URL`, `KECHAIN_TOKEN` (or `KECHAIN_USERNAME` and `KECHAIN_PASSWORD`), and `KECHAIN_SCOPE_ID` (or `KECHAIN_SCOPE`) (#185). This is ideal for `pykechain` scripts in the KE-chain SIM, as we provide support for this to make your scripting experience in KE-chain buttersmooth. An example:

    >>> from pykechain import get_project
    >>> project = get_project(url='http://localhost:8000', username='foo', password='bar', scope='Bike Project')
    >>> print(project.name)

 * Added additional checks for the `Client` to check if the url provided is correct (#185).
 * Improved the state of the project on codacy, a nice code quality monitor, from B to A grade. Removed over 100 insecure code elements, according to codacy. See: https://www.codacy.com/app/KE-works/pykechain/dashboard (#187).
 * Updated dependent versions of pyopenssl to 1.1.2 (#188), pytest to 3.2.2 (#183) and tox to 2.8.2 (#184).
 * Updated coverage of the files to internal standards. The critical models are now 100% tested such as the `Client`, `Activity` and `Part`. (#190) see: https://coveralls.io/github/KE-works/pykechain.

1.11.1 (4SEP17)
---------------
 * Added the ability to clear and attachment field (unlink the attachment). Please refer to the `AttachmentProperty.clear()` method.
 * Ensured a more robust updating of property value all over by altering `Property._value` and `Property._json_data['value']` after you set a value on a property.

1.11 (4SEP17)
-------------
 * In KE-chain 2.5 the way we use task customization has changed drastically. Pykechain (from 1.11 onwards) supports this by implementing a new concept in the activity called `Activity.customization()` (#161). This provides you an `ExtCustomization` object, which you can inspect and add new widgets. Please see the documentation on `ExtCustomization` and `Activity.customization()` for more details. An example to use is:

    >>> activity = project.activity(name='Customizable activity')
    >>> customization = activity.customization()
    >>> part_to_show = project.part(name='Bike')
    >>> customization.add_property_grid_widget(part_to_show, custom_title="My super bike"))

 * Removed previously announced deprecated method for `activity.create_activity()` (use `Activity.create()`).
 * Added deprecation warnings when using `InspectorComponent` objects and old style `Customization` components. They will be removed in November 2017 (introduced in pykechain 1.9)
 * Added the ability to retrieve a list of project members and managers with the `Scope.members()` method (#169)
 * Added the ability to manage member and managers of a scope. See the `Scope.add_member`, `add_manager`, `remove_member`, `remove_manager` (#175)
 * Added the ability to add additional keyword arguments for the methods `Part.update()`, `Part.add_with_properties()` and `Part.edit()`. This will allow to provide additional (including undocumented) arguments to the KE-chain API. (eg. 'suppress_kevents=True') (#177)
 * Added the ability to edit the name of the property, its description and the unit (#146, PR #179)
 * Added classification enumeration (#175)
 * Updated the documentation structure to better access all the pykechain models related documentation. See http://pykechain.readthedocs.io/en/latest/developer_api.html
 * Updated dependent version of tox to 2.8.0 (#178) and further to 2.8.1 (#180)
 * Updated all tests such that our coverage aim of 96%+ is maintained.

1.10.3 (28AUG17)
----------------
 * Corrected the creation of partmodels (`Part` with category `MODEL`) with multiplicities other than `ZERO_MANY` as the provided multiplicity option was not respected in the `create_model()` method of `Client` and `Scope`. Thanks @raduiordache for the find. (#170)
 * Updated tests.

1.10.2 (22AUG17)
----------------
 * Corrected the ability to assign multiple assignees, using a list of assignees to an activity using the `Activity.edit()` method. (#167)
 * Updated tests.

1.10.1 (18AUG17)
----------------
 * updated incorrect tests related to `Activity.associated_parts()`. (#96, #149)

1.10.0 (18AUG17)
----------------
 * Ability to edit the status of an `Activity`. Please refer to the `ActivityStatus` enumerations. (#163)
 * Ability to sort properties of a `Part` model. (#141)
 * Upgraded the requirements of dependent packages for development. (#152, #160, #159, #153, #157, #154)
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
