Change Log
==========

v4.1.0 (24MAY22)
----------------
* :star: Added the method to create workflow in a certain project. `Client.create_workflow(scope=...)` or `Scope.create_workflow()`.
* :+1: dependent versions for development: coverage (6.4)

v4.0.3 (24MAY22)
----------------
* :+1: Ensuring that the order attribute is removed from sidebar items in sync with the deprecation of the order in backend.

v4.0.2 (10MAY22)
----------------
* :+1: Fixed a small decoding issue which was causing prefilters to be double encoded when copying/moving a part. (#1148)
* :+1: dependent versions for development: pre-commit (2.18.1), jsonschema (4.5.1)

v4.0.1 (5MAY22) Patch Release
-----------------------------

Small patch release with a fixed MANIFEST file.

v4.0.0 (5MAY22) FORMS Release
-----------------------------

This is version 4 of pykechain in sync with the "Forms Release" of KE-chain. We added a number
of features to this release that is in full sync with the general availability of Forms in KE-chain.
The most dominant features are `Form`, `Workflow` with their `Transition`'s and `Status`-es and a
greatly improved `Context` featureset.

* We added the feature equivalence in pykechain for KE-chain Forms and Workflow.
* :star: Added the `Forms`, `Workflow`, `Transition`, and `Status` classes. (#1100)
* :star: Added multiple `Forms` methods such as `link_contexts`, `unlink_contexts`, `clone_cross_scope`, `apply_transition`, `set_status_assignees`. (#1114)
* :star: Added additional `Form` methods such as `has_part` and `compatible_within_scope`. (#1108)
* :star: Extended the `DashboardWidget` with the form numbers and charts (#1123)
* :star: Added the `FormReferenceProperties`. (#1098)
* :star: Added the `ContextReferenceProperties`. (#1099)
* :star: Added the concept of a `StatusReferencesProperty`.
* :star: Added 'Forms', 'Form models', 'Contexts' and 'Workflows' sidebar buttons in the `SideBarManager' and added ability to specify 'minimum_access_level' and 'alignment' per 'SideBarButton'. (#1103)
* :star: Added the concept of a sidebar card to the sidebar.
* :star: Added the Form Classification on the parts world.
* :star: Added the ability to create a user from the frontend.
* :star: Added the ability to request a change password link from the frontend.
* :+1: Removed the `target_scope` parameter when cloning inside the same scope

Backward incompatible changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* :+1: We discontinued support for python version 3.6.

v3.18.2 (28APR22)
-----------------
* :+1: We increased the timeout for downloading PDF's to 180 seconds per default. We futhermore add the ability to set a custom timeout on the `Activity.download_as_pdf()` method.

v3.18.1 (14APR22)
-----------------
* :+1: We are now allowing request parameters such as `size` to be passed through the `property_attachment.save_as()` function in order to resize the images on download (#1138)

v3.18.0 (22MAR22)
-----------------
* :+1: we upgraded all code to python 3.6 and higher preferred style. See the implemented improvements found throughout the code: https://github.com/asottile/pyupgrade/blob/master/README.md#implemented-features. We also reformatted the code using black.
* :+1: added tests to check if the prefilters of `ScopeReferenceProperties` are copied correctly (#842)
* :bug: Added the `offset` parameter in the request of generating a PDF, such that `Datetime` objects are rendered correctly (#1129)
* :+1: dependent versions for development: pytz (2022.1), pytest (7.1.1), mypy (0.941), coverage (6.3.2), sphinx (4.4.0), pre-commit (2.17.0), nbsphinx (0.8.8), tox (3.24.5), requests (2.27.1), jsonschema (4.4.0), pytest-xdist (2.5.0), twine (3.7.1).

v3.17.1 (29NOV21)
-----------------
A re-release of v3.17.0 due to missing version information and changelog info in the library itself. No new code.

v3.17.0 (29NOV21)
-----------------
* :+1: When a part is searched that on its `id` or `pk` than the `Client.part()` call will perform a API call to the detail route of the part api. This will greatly reduce the overhead on large databases and improve performance. (#1064)
* :+1: dependent versions for development: sphinx (4.3.1), twine (3.6.0), coveralls (3.3.1), coverage (6.2)

v3.16.0 (9NOV21)
________________
* :bug: Fixed a bug that caused the prefilters applied on `Part reference` properties to no work if the `Part` contained a comma or other special characters (#1054)
* :+1: dependent versions for development: jsonschema (4.2.0), twine (3.5.0), coveralls (3.3.0)

v3.15.0 (12OCT21)
-----------------
* :+1: Added the FormMetapanel widget to the allowed list of widgets in preparation of the introduction of the Forms world.
* :+1: Added the `cameraInputScanner` representation object to the code.
* :+1: Added extra validation checks on prefilters inside the `Paginated Widgets`. Warnings are now provided if the filter type and property value do not match correctly. (KLO-36, #1045)
* :+1: Added the attribute `showNameAndDate` on the `Signature Widget`. Defaults to True. (#1037)
* :+1: Updated the documentation for the newer concepts included over the past time.
* :+1: dependent versions for development: pytz (2021.3), pytest-cov (3.0.0), jsonschema (4.1.0), flake8 (4.0.0), tox (3.24.4)

v3.14.0 (22SEP21)
-----------------
* :bug: Fixed a bug that was causing the part reference properties to not be copied correctly. (PROJ-241)
* :+1: Improved speed of the code by a different way of validation of the property options. We validated the property options using jsonschema validation on every instantiation of the property and that is overkill. Now we do it once we are updating the property itself. (#1029)
* :+1: Added py.typed to the bdist package to indicate that pykechain supports typing. According to PEP-561.

v3.13.1 (24AUG21)
-----------------
* :+1: Add additionally a `UsePropertyNameRepresentation` including additional testing for empty `config` objects inside the `Representation`. (KE-1239)

v3.13.0 (23AUG1)
----------------
* :star: We added filter `tags__contains` to `Context` (KE-1054)
* :+1: Added the `usePropertyName` property representation to sync with the possibilities in the backend. (KE-1239)
* :+1: dependent versions for development: requests (2.26.0), nbsphinx (0.8.7), coveralls (3.2.0), tox (3.24.3), sphinx (4.1.2), pre-commit (2.14.0), twine (3.4.2)

v3.12.0 (1JUL21)
----------------
* :star: We added the `Context` object to pykechain that has full API access to the `Context` API in KE-chain v2021.6 and newer. You can add time period contexts, static location contexts and textlabel contexta and put them under a `context_group` if desired. This `Context` feature is now implemented limitly for `Activities` but in the coming period will be extended to support extensive usecases for the Forms NG featureset that is coming this fall. (KE-925)
* :bug: Fixed a test cassette that was failing on a date check. Made it use a fixed date rather than doing it on today.
* :bug: Fixed automatic compilation of the pykechain documentation on https://readthedocs.org/projects/pykechain/.
* :+1: From now on python 3.5 is deprecated. The lowest version we support is Python 3.6. We can now start to insert f-strings and variable type annotations in our pykechain codebase.
* :+1: refactoring all models that were shadowed with a `<classname>2` to enable fast and smooth deprecation in July 2021.
* :+1: We converted all type annotations in comments to proper type and variable annotations.
* :+1: When connecting to a server with a SSL certificate error which cannot be checked, we provide a message fast and dont retry. (KE-1052, #997)

# Backward Incompatible Changes

* We dropped support for Python versions 3.5 and lower. Python 3.5 reached end of life in Sep 2020 and no more new releases will be made. Consider upgrading to a newer version of Python. See: https://www.python.org/dev/peps/pep-0478/

v3.11.1 (15JUN21)
-----------------
* :bug: Fixed an issue related to setting prefilters on a `ScopeReferenceProperty`.
* :bug: Fixed a bug related to a `UserReferenceProperty` not being copied over if there was a `User` already filled in. Improved the tests to cover all property types.
* :star: Added `CONTAINS_SET` filter type enum for `contains`.

v3.11.0 (27MAY21)
-----------------
* :star: It is now possible to create, retrieve, edit and delete `ExpiringDownloads` using the `Client` and `Class` methods.
* :star: Added the GeoCoordinate representation for Geojson properties. We can now represent a geocoordinate as approximate address, Rijksdriehoekstelsel RD Amersfoort, as decimal degrees and degrees minutes seconds.
* :bug: Formatting of prefilters using lists in the `ScopeFilter` class is now based on comma's.
* :+1: Correctly formatted datetime strings are now accepted as valid datetime values.
* :+1: dependent versions for development: pytest (6.2.4), nbsphinx (0.8.5), coveralls (3.1.0), tox (3.23.1), flake8 (3.9.2), sphinx (4.0.2), pytest-cov (2.12.0), pre-commit (2.13.0), pydocstyle (6.1.1)

v3.10.1 (01APR21)
-----------------

* :bug: Copying multiple attachments using the `part.copy()` method caused the temporary directory to be removed.

v3.10.0 (29MAR21)
-----------------

* :star: It is now possible to create a `TasksWidget` with the new `add_tasks_widget` method to the `WidgetsManager` class. The enums `TasksAssignmentFiltersTypes` and `TasksWidgetColumns` support the inputs to this method.
* :star: It is now possible to create a `ScopemembersWidget` with the new `add_scopemembers_widget` method to the `WidgetsManager` class.
* :bug: For grid widgets, corrected name of field `incompleteRowsVisible` to `incompleteRowsButtonVisible`.
* :bug: Widgets created with the `create_widgets` method of the `WidgetsManager` class now append the internal `_widgets` attribute.
* :bug: Added allowed use of `Autofill` representation object on `UserReferenceProperty` classes.
* :bug: Creating of new activities was performed using `data` instead of `json`. Now, `None` values are cleared and the request allows `kwargs`.
* :+1: The order of `Part` instances returned from the `Client._create_parts_bulk()` method is now guaranteed to match the request.
* :+1: Datetime properties can now be set using (valid) string values.
* :+1: Added `now_in_my_timezone` method to the `User` class, to retrieve the current time based on the timezone of that user.
* :+1: The input `collapse_filter` in the `add_filteredgrid_widget` method now accepts the input `None` to fully hide the filter panel.
* :+1: Expanded `ScopeFilter` options to the support the following `Scope` attributes: tag, status, name, team, due date, start date and progress.
* :+1: Added file path as return value of the `download_as_pdf` method of the `Activity` class.
* :+1: Added `status` keyword to the `ScopeFilter` class. All filters are now parsed and written to option dicts internally, encapsulating the property-specific format of the filters.
* :+1: dependent versions for development: pytest (6.2.2), pytz (2021.1), mypy (0.812), nbsphinx (0.8.2), coveralls (3.0.1), tox (3.23.0), flake8 (3.9.0), twine (3.4.1), sphinx (3.5.3), pytest-cov (2.11.1), pre-commit (2.11.1), pydocstyle (6.0.0)


Improved the `copy` and `move` methods of the `Part` class.

* :bug: Part reference properties with a value set to the copied Part's children will no longer refer to the original child Parts. That is, such "internal" references are updated with the new child Parts.
* :+1: `move` now makes use of the `copy` method directly, simplifying the `move` method and reducing duplicate code.
* :+1: More efficient use of `populate_descendants` and other bulk operations when cloning the data model.
* :+1: Refreshing a `part` now also refreshes its `properties` in-place, instead of creating new Python objects.
* :+1: Added `DeprecationWarnings` to the original, public functions, for deprecation in July 2021.

Backwards incompatible changes:
-------------------------------
* In case a `Part` model is copied to a `target_parent` model with zero (or more than one) instances, using `include_instances` now results in an `IllegalArgumentError`. Previously, zero parents would not produce any instance and multiple parents would create duplicate instances.


v3.9.5 (23DEC20)
----------------

* :bug: Any `kwargs` in the `count_children()` methods of the `Activity` and `Part` classes were not being forwarded to the actual function. Now filters such as `name__contains` are properly supported.

v3.9.4 (23DEC20)
----------------

* :star: Implemented `download_as_excel` method to the `Widget` class, to export any grid widget as an Excel file.

* :bug: Removed multiple `return` statements from `_validate_edit_arguments` helper function in the `Activity` class, enabling usage of kwargs.
* :bug: Fixed a bug regarding the code expected to return from the back-end when calling the `share_pdf` and `share_link` functions.

* :+1: Added keyword arguments (kwargs) to the `execute()` method of the `Service` class, in order to insert contextual information into the `ServiceExecution`.
* :+1: Added `count_children` method to the `Activity` and `Part` classes for a light-weight count of the number of child objects.
* :+1: Added `include_qr_code` keyword to the `download_as_pdf` and `share_pdf` methods of the `Activity` class, to include a QR-code to the original KE-chain activity.
* :+1: Added `automatic` paper-size option for `PaperSize` enumeration class.
* :+1: dependent versions for development: sphinx (3.4.0), requests (2.25.1), pytest (6.2.1), pre-commit (2.9.3)

v3.9.3 (8DEC20)
---------------

* :bug: Fixed a wrong `MetaWidget` enum that was causing an issue when creating a `FilteredGrid` widget.
* :+1: Added `category` keywords to `edit()` method of `Scope` class and enabled providing of keyword argument to all edit methods.


v3.9.2 (3DEC20)
---------------

* :+1: Pykechain now supports Python version 3.7 and 3.8 on its `Scripts` and `Notebook` classes. Removed the support of Python 2.7, 3.5 and 3.6.

v3.9.1 (27NOV20)
----------------

* :bug: In the `Part.property()` method, the property is retrieved by matching a `name` prior to matching a `ref`, to prevent conflicts when these might identical between different properties.
* :bug: The `text` and `is_active` inputs for editing of a `Banner` were not properly managed, leading to API errors or unchanged values.
* :bug: Batched property values of `BaseReference` and inherited classes are now stored as lists of dicts instead of list of UUIDs, to simulate values retrieved directly from KE-chain.
* :bug: Resolved small issue where `empty` values were being combined with normal objects in the `edit_cascade_down()` method of the `Activity` class.

* :+1: Refactored a lot of the strings used in the `Widget` meta into enums, to help with consistency.
* :+1: Retrieving the `value` of any reference property is now performed in batches to limit request size, using the existing `get_in_chunks` utility function.
* :+1: Editing the `title` and `meta` of a `Widget` can now be performed simultaneously and `title` can be cleared by providing `None`.
* :+1: Added input validation and additional tests for `update_widgets()` method of `Client` class.
* :+1: Set identical type hinting for `title` keywords in all methods of the `WidgetsManager` and `Widget` classes.
* :+1: In the `set_prefilters()` and `set_excluded_propmodels()` methods of the `MultiReferenceProperty` class, users can now provide the referenced model to validate against, or bypass validation altogether, using the `validate` input argument.
* :+1: The `child()` method of the `Activity` class now tries to find a cached child prior to requesting the child from KE-chain, similar to the `Part` class.

Backwards incompatible changes
------------------------------

* As planned and marked with a PendingDeprecationWarning we deprecate the customizations of Activities. This can only be done with old KE-chain versions which are no longer available in production.
* Deleted enumeration class `ComponentXType`

v3.9.0 (05NOV20)
----------------

* :star: Added the option to manage supervisor members on a scope for KE-chain 3 backends that support the supervisor member users. That is possible for releases of KE-chain 3 starting from June 2020. (version 3.7). #772
* :star: Added the possibility to create a `ServiceCardWidget` through the `add_service_card_widget()` function.
* :star: Added the possibility to create a `DashboardWidget` through the `add_dashboard_widget()` function.

* :bug: Updating or setting of widget associations with only readable and/or writable properties is now supported.
* :bug: Missing upper-case letter in `SideBarManager` caused a loss of the `override_sidebar` property.
* :bug: `SidebarButton` class did not preserve all data from the scope options, losing display names in other languages. Editing of this values is now possible as well.
* :bug: Added a check whether the value of a single or multi select list `Property` is in the options when copying or moving a `Part`.

* :+1: Created `PropertyValueFilter` class to manage (pre)filters of `MultiReferenceProperty` and `FilteredGridWidget` objects.
* :+1: Created `ScopeFilter` class to manage (pre)filters of `ScopeReferencesProperty`.

* :+1: Added `refresh()` method on `SideBarManager` to reload the side-bar from KE-chain.
* :+1: Added `get_prefilters()` and `set_prefilters()` method to all reference property classes by default, albeit raising a `NotImplementedError`. Implementations exist for `ScopeReferencesProperty` and `MultiReferenceProperty`.
* :+1: Added `get_excluded_propmodel_ids()` method to the `MultiReferenceProperty` class.
* :+1: Added `alignment` keyword arguments for the creation of `ServiceCardWidget` and `ServiceWidget` classes.
* :+1: Added `ref` keyword to `create_activity()` method of `Client`

Backwards incompatible changes
------------------------------

The following changes are not compatible with previous functionality:

* Changed the way edit functions work for `Part`, `Properties`, `Activity`, `Scope`, `Notification`, `Service`, `Team` and `Banner` classes. Passing inputs with value None in those functions will clear those attributes if possible. Not mentioning them will not overwrite their values.
* The `overwrite` keyword argument in the `set_prefilters()` method of the `MultiReferenceProperty` now only overwrites prefilters if explicitly provided with new ones. Removing all prefilters is now supported with the keyword argument `clear`, also a boolean.
* Specifying prefilters via separate lists of properties, values and filter types is planned to be deprecated in January 2021 in favor of using `Filter` objects as input.

v3.8.2 (18SEP20)
----------------

* :bug: The `descendants` of a `Part` with classification `CATALOG` returns both the Catalog and Product descendants. This broke the guaranteed parent-child relationship when populating the descendants in the `populate_descendants()` method of the `Part` class.
* :bug: KeyError in `add_with_properties()` method of the `Part` class.
* :+1: dependent versions for development: pytest (6.0.2)

v3.8.1 (08SEP20)
----------------

* :bug: Added `title_visible` property to `Widget` class for the widget's title shown in KE-chain, deprecating the `default_title` mechanism when creating widgets. The default title of a widget is dependent on front-end and is not stored in the widget.
* :bug: Set and Update of widget associations now handles optional `part_instance_id` and/or `parent_part_instance_id` inputs.
* :bug: `WidgetsManager` and `PartSet` no longer implement `Iterable` as an "iterator", making it possible to loop over the Widgets/Parts multiple times.
* :bug: `add_signature_widget()` method of the `WidgetManager` class now creates an editable signature widget by default. The new input argument `editable` can be set to False to create a viewable widget.

* :+1: Added `update_activities` method to `Client` to update activities in bulk.
* :+1: `WidgetsManager` is now stored in its `Activity` object for lazy retrieval, while the `WidgetsManager` now explicitly stores a reference to its `Activity`.
* :+1: Available `Part` options of a pre-filtered multi-reference properties are now filtered when using the `choices()` method on the `MultiReferenceProperty`.
* :+1: Added `model_id` attribute to `Part` class.
* :+1: Added `count_instances()` method to the `Part` class, to retrieve the number of Part instances of a Part model.
* :+1: Added `get_landing_page_url()` method to the `Scope` class, to retrieve the (relative) URL of landing page for that scope. Append it to the client's API root for a full URL.
* :+1: Added `LanguageCodes` enum class to enumerate the available Language options for user profiles.
* :+1: Added `value_ids()` method to `_ReferenceProperty` class, returning a list of UUIDs instead of Pykechain objects.
* :+1: Added lazy retrieval in `parent()` method of `TreeObject`, `Part` and `Activity` classes. Retrieving children or populating descendants also sets all known parent objects.
* :+1: Inverted the inheritance hierarchy of Class2 classes, allowing for type-checking via `isinstance()`. However, creating objects from these classes is no longer supported.
* :+1: Added `set_associations` and `remove_associations` method to the `Widget` class (#827)
* :+1: Renamed activity clone API endpoint is now supported. We now support the cloning and renaming of Parts as well as cloning the activities. (#805)
* :+1: Added support of user references and scope references properties in pykechain by implementing the `UserReferencesProperty` and `ScopeReferencesProperty` classes. (#832)
* :+1: Included pending deprecation of version-2 classes such as `Part2`, `Property2`. It is advised to use the original `Part` and `Property` classes instead. (#713)
* :+1: dependent versions for development: sphinx (3.2.1), pytest-cov (2.10.1), tox (3.20.0), pydocstyle (5.1.1), pre-commit (2.7.1), coveralls (2.1.2)

v3.8.0 (11AUG20)
----------------

* :star: Added the bulk_create_parts API endpoint, which allows the adding of multiple `Part` instances with `Properties` in one call. #797
* :star: Added the bulk_delete_parts API endpoint, which allows the deletion of multiple `Part` objects in one call. #812
* :+1: Implemented robust method to update Scope side-bar buttons with minimum number of requests using a context manager (e.g. `with scope.sidebar as manager` mechanism) (#654)
* :+1: Included mapping dict from KE-chain native pages to their Font Awesome icons.
* :+1: Added properties to retrieve the root Activity and Part objects of a Scope. (#799)
* :+1: Added bulk-clone of activities, including associated data models. (#737)
* :+1: Added `upload` input value for when creating basic- and filtered-grid widgets. (#814)

v3.7.6 (30JUN20)
----------------

* :star: Added the Weather Widget creating possibilities. #788
* :+1: dependent versions for development: tox (3.16.0)

v3.7.5 (29JUN20)
----------------

* :star: Added the Weather and GeoJSON property types to pykechain in correspondance with the backend version (core.pim 3.6.0). #787
* :+1: dependent versions for development: mypy (0.782), requests (2.24.0), nbsphinx (0.7.1), semver (2.10.2)

v3.7.4 (15JUN20)
----------------

* :bug: Reloading `Activity2` when retrieved in an `ActivityReferencesProperty` in order to populate it with all required data.
* :+1: dependent versions for development: sphinx (3.1.1), pytest-cov (2.10.0)

v3.7.3 (11JUN20)
----------------

* :+1: Added `autofill` representation for date, time and datetime properties (#733)
* :+1: Added `breadcrumb_root` option for meta-panel widgets.
* :+1: dependent versions for development: sphinx (3.1.0), flake8 (3.8.3), pre-commit (2.5.1)

v3.7.2 (8JUN20)
---------------
* :bug: fixed an issue where an old version of the dependent 'semantic versioning' package (`semver`) could cause problems. We now put a proper versioning requirement in the setup.py such that the correct version will be installed. Thanks for @bastiaan.beijer for finding this one.
* :+1: dependent versions for development: tox (3.15.2)

v3.7.1 (4JUN20)
---------------

* :bug: Reference properties values can now be set with identifiers, such as `property.value = "1234..."` and a list of identifiers, such as `property.value = ["1234..."]`. The original behavior of the `MultiReferenceProperty2` was inconsistent: the `value` attribute did not allow strings while updating via the `Part2.update()` and `Part2.add_with_properties()` methods allowed it. (#770)
* :+1: Enabled kwargs for bulk editing of activities. (#770)
* :+1: Assigned `Part2` class as the referenced class for the `MultiReferenceProperty2` for more precise type-checking. (#770)

v3.7.0 (3JUN20)
---------------

This is a big release and perfectly qualifies for a minor version number upgrade. We took care of many things and improvements in alignment with fresh and refreshed capabilities of the KE-chain 3 platform.

In this release we also deprecated functionality that were announced to be deprecated some time ago. We deprecated all compatibility to 'KE-chain 2'. Please refer to the Backward Incompatible Changes down below.

:star: is a new feature
:+1: are improvements
:bug: are fixed bugs./

* :star: Extracted representations from `Property2` class into a separate `RepresentationMixin` class. This is now utilized by the `Scope2`, `Activity2` and `Property2` classes.
* :star: Implemented `MultiSelectListProperty2` class, generalizing the implementation of the `SelectListProperty2 class. Intermediate class `_SelectListProperty` now hosts the generic implementation. #732
* :star: Implemented `ActivityReferencesProperty` class, generalizing the implementation of the part reference `MultiReferenceProperty2` class. Intermediate classes `_ReferenceProperty` and `_ReferencePropertyInScope` have been added for further reference properties. #746
* :star: Added `ScopeRoles` and `ScopeMemberActions` enum classes to list the roles of and operations on scope members.

* :+1: Added `PropertyTypes` enumeration values for the JSON property and multiple new reference properties.
* :+1: Added `CustomIconRepresentation` to change the font-awesome icons of KE-chain scopes and activities. Default icon display mode is set/gettable, defaulting to "regular".
* :+1: Added `show_name_column` input to the `add_supergrid_widget` method of the `WidgetsManager`.
* :+1: Added `show_download_button` and `show_full_screen_button` inputs to the `add_attachmentviewer_widget` method of the `WidgetsManager`.
* :+1: Added `link_value` input to the `add_card_widget` method of the `WidgetsManager`. Linking to sub-process activities now opens the link in tree view by default.
* :+1: Created mapping table `property_type_to_class_map` to convert between property types from the `PropertyType` enumeration and property classes derived from the `Property2` class.
* :+1: Added `BaseInScope` base class for KE-chain objects limited to a single scope. It inherits from `Base` itself. The new class is used for Parts, Properties, Activities, Widgets, Associations and Services. Original class is still used for Scopes, Teams, Users, Banners, Notifications and ServiceExecutions.
* :+1: Moved `scope` property method to the `BaseInScope` class, adding lazy retrieval to limit overhead.
* :+1: Improved robustness of teardown for tests for the `Scope2` class.
* :+1: Added `editable` argument to the `add_attachmentviewer_widget` method of the WidgetsManager, to enable both viewing and editing of the attachment.
* :+1: Added `show_log` argument to the `add_service_widget` method of the WidgetsManager, to separate the log file and log message.
* :+1: Added `Alignment` enum class, leaving `NavigationBarAlignment` as wrapper for backwards compatibility.
* :+1: Added intermediate `create_configured_widget` method in WidgetsManager  for widgets with associated properties.
* :+1: Moved all inherited `Property` methods into the `Property2` class and removed Property as its superclass.
* :+1: Large clean-up for user-input validation for most `Client` methods to provide consistent error messages.
* :+1: Added intermediate `_retrieve_singular` method in `Client` class to simplify other methods intended to get 1 object. These other methods all had identical dependency on methods to retrieve more than 1 object, such as `part()` on `parts()`.
* :+1: Improved traceback of any `APIError` by printing content from the `response` and/or `request` if provided by keyword arguments, e.g. `APIError("Incorrect value!", response=response)`. (#742)
* :+1: dependent versions for development: semver (2.10.1), pytest (5.4.3), pytest-cov(2.9.0), Sphinx (3.0.4), nbsphinx (0.7.0), tox (3.15.1), flake8 (3.8.2), pre-commit (2.4.0), mypy (0.780), removed PyOpenSSL which was only for python 2.7.

* :bug: Editing an `Activity2` now uses its `__init__` to refresh with the JSON from the response, removing an additional reload to get updated values.
* :bug: Added `Activity2.scope_id` setter method (self-induced bug due to the introduction of `BaseInScope`).
* :bug: Moved the serialization of property values from the `Part2._parse_update_dict()` method to the new `Property2.serialize_value()` method. This new method is used in the `_put_value()` method of this class to have identical serialization in both `value` and `part.update()` mechanics.
* :bug: The bulk update of property values via the `use_bulk_update` attribute and `update_values` method now uses the same serialization pipeline as synchronous updating. Also made the attribute a `Property2` class property, converting it to a singleton.
* :bug: Refactored the `reload` method of the `Client` class to be able to reload any Pykechain class object. #760
* :bug: Scope edit cleared some properties from the scope if they were not provided.

Backwards incompatible changes
------------------------------

We deprecated the following:

* `get_all_children` helper function for parts and activities. Use the `all_children` method instead.
* The `MultiReferenceProperty2.choices()` method now returns an empty list if no `Part` model is yet configured. Now the method no longer raises a TypeError (i.e. 'NoneType' object is not subscriptable).
* We deprecated the `ActivityTypes`: `USERTASK`, `SERVICETASK` and `SUBPROCESS` from `ActivityType` enum class.
* We deprecated the option to use `START` from `NavigationBarAlignment` enum class.
* We deprecated the mapping table `WIMCompatibleActivityTypes`.

v3.6.4 (20APR20)
----------------

* :bug: removed use of the old API usage of `descendants`. (#741)
* :+1: We will now raise the correct errors when retrieving an `active banner`. (#741)
* :+1: We now use actual depth-first sorting of children. (#741)
* :+1: For testing and development: Less hard-coded and centralized teardowns, using `assertEqual(expected, received)` format. (#741)
* :+1: dependent versions for development: Sphinx (3.0.2), nbsphinx (0.6.1)

v3.6.3 (14APR20)
----------------

* :+1: Added `current_user()` method on the Client class to return the `User` object of the user connected to KE-chain.
* :+1: Added various arguments to the `create_notification()` method.
* :+1: Added `edit()` method to the Notification class.
* :bug: Removed old API usage of `descendants` from `copy()` of the Part class.
* :bug: Raising correct errors whenever no (or multiple) active banner exist in the `active_banner()` method.

v3.6.2 (27MAR20)
----------------

* :bug: We found out that the regex to validate the email addresses was incorrectly defined. We added additional tests to fix this. (thanks to @jberends for the omission and the fix)

v3.6.1 (UNRELEASED)
-------------------

This was never released due to some inappropriate tagged.

v3.6.0 (26MAR20)
----------------

This minor releases adds two new concepts (:star: :star:) that also exist in the KE-chain backend. We added a `Banner` concept that allows powerusers
to set an announcement banner which is displayed (and can be dismissed) in KE-chain for all logged-in users within a certain timeperiod. We also added the concept of a `Notification` in KE-chain, where email or in-app notification can be displayed suchs as sharing a link of
a task to another user, or sharing a PDF of a task to another user or and external email address.

* :star: Implemented `Banner` model and methods to create, delete and retrieve them. #725 (Thanks to @jelleboersma for the implementation)
* :star: Added the concept of a `Notification` including the possibility to retrieve, create(send) and delete `Notifications`. #467 (thanks to @raduiordache for the implementation)
* :star: Added the possibility to share a link or PDF of an activity using the `Activity2.share_pdf()` or `Activity2.share_link()`. #467 (thanks to @raduiordache for the implementation)
* :bug: When adding a new `Activity2` to a parent, it will now cache its childeren in case the parent also have the children cached. In essence it updates the `_cached_children`. #722 (thanks to @jelleboersma)
* :+1: dependent versions for development: pytest (5.4.1), mypy (0.770), tox (3.14.6)

v3.5.4 (9MAR20)
---------------

* :star: implemented retry on connection errors for the `Client`. This will ensure that if the client connection to the server has been dropped, the client will retry the request again with an exponentional backoff not to overload. #714
* :+1: dependent versions for development: sphinx (2.4.4)

v3.5.3 (27FEB20)
----------------

This is release :100: of pykechain! That means :cake:!

* :bug: Fixed a bug where the API parameters for the `Service` now includes additional attributes on its objects. #709. Thanks to @bastiaanbeijer and @raduiordache for finding it and @jelleboersma for providing the fast resolution.

v3.5.2 (26FEB20)
----------------

* :bug: Fixed a bug in the multi references property where the call made to the backend with a normal user would require more information than only the id's of the parts, this resulted in an API error in the retrieval of the referred instances. #707 Thanks @BastiaanBeijer for the discovery and @JelleBoersma for the quick fix.
* :bug: `child()` method of Part2 now robustly retrieves child parts created after retrieval of the parent itself, regardless of the `_cached_children`.

v3.5.1 (25FEB20)
----------------

* :bug: Default widget title is now respected when widgets are created with `title=False`.
* :+1: Improved typing of `TreeObject` methods in its subclasses.

v3.5.0 (24FEB20)
----------------

This release brings some interesting changes to pykechain. We discovered suddenly that the `Activity` and `Part` where actual trees, being a sustainable company, we also implemented them as such. You will find additional helper methods on both models such as `child()`, `all_children()`, and `siblings()`. This release also bring many small updates from two 'bug hunting' pull requests.

* :star: Creation of `Widgets` without a title but with a reference (or `ref`) now supported via the `show_title_value` keyword.
* :star: Implemented `child` method for `Part2` and `Activity2` class. Also implemented "dunder" method `__call__()` as short-hand for `child()`, making tree searching much simpler to code, e.g: `child = root('part')('child')`
* :star: Creation of `Widgets` without a title but with a reference (or `ref`) now supported via the `show_title_value` keyword.
* :star: Added `Association` class and retrieval method `associations()` on the `Client` class.
* :bug: Creation of `Activity` now uses parent's `classification` if provided.
* :+1: Deprecated `get_all_children` helper function. It is replaced by the `all_children` method on the `Part2` and `Activity2` classes.
* :+1: Added `classification` attribute to the `Part2` class.
* :+1: Added caching of children to the `Activity2.children()` method.
* :+1: Moved creation of WidgetsManager instances from the `widgets()` method of the Client to Activity class. The Client's method output is now consistent with the `create_widget(s)` methods. #693
* :+1: Moved `delete_widget(s)` methods from WidgetsManager to Client class.
* :+1: Refactored Widget's `delete` method to now calls its WidgetManager, if available, to maintain a consistent Widget list.
* :+1: Added `__contains__` method to WidgetsManager to support "widget in manager" comparisons.
* :+1: Creation of `Activity` now uses parent's `classification` if provided.
* :+1: Added `page_size` input to the `add_scope_widget` method of the WidgetManager class to set the pagination of the `Scope` widget.
* :+1: dependent versions for development: sphinx (2.4.3), pre-commit (2.1.0), requests (2.23.0)

Backward incompatible changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* The `Client.widgets()` method now returns a list of `Widget` objects. In the past this was a `WidgetsManager` object that contained additional helper/widgetfactory methods to instantiate a widget. This is now brought in line with other `Client` widget methods like `Client.create_widget()`, etc. (reg #693)


3.4.0 (17FEB20)
---------------

* :star: Added `Client` method for the bulk-update properties API endpoint. #663
* :star: Added `Property2` flag `use_bulk_update` and class method `update_values` to support bulk-update of property values while still using the `value` attribute. #663
* :bug: `has_value` method of the `Property2` class now accurately predicts floats, integers and boolean values. #675
* :bug: `value` attribute of `AttachmentProperty` class now refreshes automatically when uploading attachments. #675
* :+1: moved bulk-update of widgets to the client. Also split the `_validate_widget` and the `_validate_related_models` Client methods. #658
* :+1: Updated `populate_descendants()` to use new API and actually store the `_cached_children`.
* :+1: Added test to confirm a value of `None` clears a reference property. #468
* :+1: Keyword-arguments provided when creating widgets via the `WidgetsManager` do now propagate successfully.
* :+1: Improved unittests for `Property2`, `AttachmentProperty2` classes.
* :+1: dependent versions for development: semver (2.9.1), coveralls (1.11.1), Sphinx (2.4.1), tox (3.14.5)

3.3.2 (6FEB20)
--------------
* :bug: `Activity2` method `_validate_edit_arguments` now correctly checks for members of the scope prior to assigning new assignees.
* :star: added thousand separators representation on numeric properties to pykechain. #670 (thanks to @raduiordache)
* :+1:Fix the `Widget.parent()` method call. #655
* :+1:Updated `populate_descendants()` to use new API and actually store the `_cached_children`. #662
* :+1: dependent versions for development: pydocstlye (5.0.2), nbsphinx (0.5.1), pytest (5.3.5), pre-commit (2.0.1)

3.3.1 (8JAN20)
--------------
* Fixed a lingering performance issue with `Part.add_with_properties()`. In older KE-chain API versions a full part refresh was needed in order to re-retrieve the attributes of a `Part`. In the current backend API this is not needed anymore. The attribute that caused this was the `refresh` flag in the `Part.add_with_properties` method call and resulted in the re-retrieval of all children of a part and caused longer cycle times once the list of children grows longer (linear). This flag will be deprecated in the next release. Currently all Parts are automatically refreshed with information from the backend in a lightweight manner (without an extra API call). The part just created with the method `add_with_properties` is added to the `Part`'s children automatically if the children of the parent are already once retrieved (and cached). Many thanks to our committed users / customers for finding this and pointing this out.
* Updated type hinting for all methods for `Part2` objects, to assist the user in capable Python Development Environments (IDE's - such as Pycharm or VSCode) to write error-free code.
* Added a Pending Deprecation Warning when setting the `refresh` attribute on the `Part.add_with_properties(refresh=False/True)`. It will be removed in version 3.4 and an DeprecationWarning Exception will be raised then.

3.3.0 (7JAN20)
--------------
* Added scope widget button customization in the `WidgetManager` method `add_scope_widget`.
* Added native KE-chain pages as option for the `Card` widget `link` value. Use the `KEChainPages` enum to set your target.
* Added `show_images` to the inputs of `add_supergrid_widget` and `add_filteredgrid_widget` methods.
* Organized function headers of the `WidgetManager` methods to match the order of the inputs.
* Added `edit_cascade_down` method to the `Activity2` class to trickle-down the changes to the attributes of a subprocess.
* Added `APP` classification options to the tasks to actively work on the `APP` screens (not end-user editable)
* Added support of Python 3.7 and 3.8 in sim scripts to support future unlocking of this feature in KE-chain 3.2 (FEB20).

3.2.4 (6JAN20)
--------------
* Feature: migrating `async` to `async_mode` for all backend api's for future compatibility. Determines if backend lives on version 3.1.0 or above. (#649)
* dependent versions for development: coveralls (1.10.0), Sphinx (2.3.1), mypy (0.761), tox (3.14.3), pre-commit (1.21.0)

3.2.3 (19DEC19)
---------------
* :bug: copying of (multiple) `1-or-many` `Part` models to the same parent is now fixed. #636 Thanks to @jelleboersma
* :bug: copy/move of a `Part` also refreshes the part to ensure all properties are copied/moved. #636
* :point_up: dependent versions for development: pytest (5.3.2), coverage (pinned to < 5.0), Sphinx (2.3.0), mypy (0.760)

3.2.2 (14DEC19)
---------------
* made `Activity.associated_parts()` great again. #523 Thanks to @raduiordache
* Added also the possibility to get the associated objects of an `Activity` with ids only. #523
* Updated dependent versions for development: pydocstyle (5.0.1)

3.2.1 (06DEC19)
---------------
This is the day after 'Sinterklaasavond' :gift: edition of pykechain.

 * Update the `Client.create_widgets` (bulk create widgets) and `Client.update_widgets_associations` (bulk update widget associations) to work seamlessly with the backend on it as we discovered a bug in the backend during tests of these methods. Additional tests where added as well. #617, #626
 * Added `SideBarManager` and `SideBarButton` classes to support configuration of the scope side-bar. #539
 * Added Enumeration classes `KEChainPages`, `SubprocessDisplayMode`, `URITarget` and `FontAwesomeMode` to support configuration of the scope side-bar. #539
 * Added `is_url` url checker, with a tap to the :tophat: for Konsta Vesterinen and his implementation of an URL validator. #539
 * Added pre commit hooks for developers. Use `pre-commit install` to install the hooks in your local repo and while committing, watch your git console (in Pycharm in the 'Version Control' tab (bottom) > 'Console' tab). If you want to run the pre-commit hooks on all files (not only those ones that changes in the commit) run `pre-commit run -a` on the command line (Terminal).

3.2.0 (03DEC19)
---------------
 * Added bulk widget creation and editing of widgets. #617 (thanks to @jelleboersma)
 * Added methods to retrieve pykechain objects from the server via 'ref'. Including services. #608. (thanks to @raduiordache)
 * Added `edit` and `delete` methods to `Team` class and fixed some bugs relating to `Team` creation. #620 (thanks to @jelleboersma)
 * Added additional inputs to create an `Activity`: `status`, `start_date`, `due_date`, `description`, `classification`. #615 (thanks to @jelleboersma)
 * Bugfix: `Part.scope()` retrieves the part's scope regardless of its status. (thanks to @jelleboersma)
 * Improved `Client` exception messages when retrieving singular objects, e.g. `Client.scope()` (thanks to @jelleboersma)
 * Updated dependent versions for development: mypy (0.750), tox (3.14.2), sphinx (2.2.2), coveralls (1.9.2 :vulcan_salute:️)

3.1.5 (29NOV19)
---------------
This is the black friday edition of pykechain.

 * Changed the default upload of a sim script to use python 3.6 when executed on KE-chain as a script.
 * Added tests for retrieving objects by `ref`. (#608 - thanks to @jelleboersma for the find and @raduiordache for the PR)
 * Updated the implementation of the `add_scope_widget()` method to support filters. (thanks to @jelleboersma)
 * Updated dependent versions for development: twine (3.1.1), pytest (5.3.1)

3.1.4 (25NOV19)
---------------
 * Updated the implementation of the `Scope.members()` method when dealing with `is_leadmember` and `is_manager` filters. (thanks to @jelleboersma)
 * Updated CI tests to use Github Actions.

3.1.3 (22NOV19)
---------------
 * Fixed the bulk editing and creating of parts (`Part2`) which have attachments in the list of properties. In the background we now separate the upload of attachments from the update of the properties. #590 (Thanks to @jelleboersma)
 * Fixed a bug with timezones.
 * Updated dependent versions for development: nbsphinx (0.5.0), pytest (5.3.0), jsonschema (3.2.0), twine (3.0.0), pyopenssl (19.1.0).

3.1.2 (14NOV19)
---------------
 * small fix for backwards compatibility of `CardWidgetLinkTarget` enum.

3.1.1 (UNRELEASED)
------------------
 * This version is never released to the public

3.1.0 (14NOV19)
---------------
 * Added `Activity2.move()` function to move an Activity somewhere else under another Activity into this code base. (#579 thanks to @raduiordache)
 * Created a framework for Property Representation, similar to the ones provided in KE-chain. Using this framework you can add representation for e.g. the SelectList, such as shown as a dropdown, checkboxes or a button. Check out the documentation on `SelectListRepresentations`. We also added `DecimalPlaces`, `SignificantDigits`, `LinkTarget` and `ButtonRepresentation`. (#532 thanks to @jelleboersma)
 * Added `FileSizeValidator` and `FileExtensionValidator` to pykechain. Now you can use it also to create these validators for `AttachmentProperty2`-ies. Also if these validators are active on properties you can use the `Property2.is_valid()` api to check if the property conforms to these validators. With `Property2.get_reason()` you retrieve the reason for the validator being either valid or invalid. This will override the patch release of 3.0.2. #573
 * Added `ImageFitValue` enum to better support the `CardWidget` and `AttachmentviewerWidget` generation and editing. #582 (thanks @jelleboersma)
 * Updated dependent versions for development: tox (3.14.1)

3.0.2 13NOV19
-------------
 * Ensured proper handling of filesize and fileextension validators in KE-chain. This is a temporary release for compatibility reasons. It will be replaced with fully blown Validators in the next release. (thanks to @bastiaanbeijer for finding it)

3.0.1 12NOV19
-------------
As we dropped Python 2.7 support we improve the code throughout on type hinting and type checking. We do this for
better code and code that is less prone to errors while developing python applications on top of KE-chain
with pykechain. This release improves the code in several places in this regard.

 * (for developers) Additional type checking and type hinting consistencies fixed (thanks to @jelleboersma)
 * (for developers) added enumerations inheritance (thanks to @jelleboersma)
 * small fix for the `Client.user()` methods that expects a `id` keyword in the backend and got a `pk`. (thanks to @jelleboersma)
 * refactored the `update_dict` for bulk actions where `fvalues` can be used such as part create with properties and part update with properties (thanks to @jelleboersma)

3.0.0 31OKT19
-------------

This is a next major release of pykechain, adding support for the legacy version of the Product Information Module (PIM) in KE-chain as well as the new version PIM3.

Backward Incompatible Changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* this version is incompatible with Python version 2.7. It will produce a `RunTimeError` when trying to execute this in ``Python 2.7``. This is due to the fact we added Python 3 type hints to the source code to improve stability.
* When connecting to KE-chain version 2 API backends, please refer to ``pykechain version 2.7``. This versions attempts to autodetect the version of the API and switch to legacy classes and methods accordingly, but YMMV. In your requirements you can place the following line: ``pykechain <= 2.7.99`` to ensure that the latest pykechain v2 is installed.

Major differences
~~~~~~~~~~~~~~~~~

 * Widgets are not part of KE-chain 3. The `Activity` object does provide a `WidgetManager` to add, remove, reorder, insert and manage `WidgetSets` in general.
 * There are some new widgets introduced, please refer to `the documentation <https://pykechain.readthedocs.io/en/latest/developer_api.html>`_
 * We have a new `Part2`, `Property2` and `Scope2` API endpoint (``/api/v3/...``). This API is faster but asks the call to be more explicit on what fields to return initially.
 * KE-chain 3 has widget level associations, and not on activity anymore. That means that parts and part models are associated per widget.
 * We made over 300 commits with updates, improvements and changes in relation to pykechain v2.

Improvements
~~~~~~~~~~~~
 * Added `clone_scope()` method to the `Client` and the `Scope` object. With the right permissions you can now clone a project using pykechain.
 * We added 'representation' for some property types in the KE-chain 3 backend. In such way we can support alternative representations of eg. single select list as a list of buttons in the frontend, greatly improving the usability on mobile devices.
 * More consistent handling of pykechain base objects throughout the code. Now you can pass in a pykechain Base subclassed object almost anywhere, where in the past you could only have passed only the UUID/id.
 * We added `ref` to most pykechain models. You can find `Properties` of a `Part` based on the `id`, `name` or `ref` now. You can also search most models for its `ref`. The `ref` is a slugified value of the original name of the object in KE-chain.
 * We enabled the options `check_certificates` in the `pykechain.helpers.get_project()` function and the `Client`. You can use this to disable the check for https certificates in pykechain, eg. to connect to the local HTTPS host or to a on-premise host that has a self-assigned certificate.
 * We added a `DatetimeProperty` to more precisely manage the conversion of datetimes back and forth with the API.
 * We added type hints on most, if not all major methods.
 * We updated the documentation.
 * We test pykechain version 3 against python 3.5, 3.6, 3.7, 3.8 and pypy3 - and naturally all tests pass.
