import bisect
import warnings
from typing import Sized, Any, Iterable, Union, AnyStr, Optional, Text

import requests
from six import string_types, text_type

from pykechain.enums import SortTable, WidgetTypes, ShowColumnTypes, NavigationBarAlignment
from pykechain.exceptions import NotFoundError, APIError, IllegalArgumentError
from pykechain.models.widgets import Widget
from pykechain.models.widgets.helpers import _set_title, _initiate_meta, _retrieve_object, _retrieve_object_id
from pykechain.utils import is_uuid, find


class WidgetsManager(Sized):
    """Manager for Widgets.

    This is the list of widgets. The widgets in the list are accessible directly using an index, uuid of the widget,
    widget title or widget 'ref'.
    """

    def __init__(self, widgets, activity, client=None, **kwargs):
        # type: (Iterable[Widget], Union[Activity, Activity2, AnyStr], Optional[Client], **Any) -> None  # noqa: F821
        """Construct a Widget Manager from a list of widgets.

        You need to provide an :class:`Activity` to initiate the WidgetsManager. Alternatively you may provide both a
        activity uuid and a :class:`Client`.

        :param widgets: list of widgets.
        :type widgets: List[Widget]
        :param activity: an :class:`Activity` object or an activity UUID
        :type activity: basestring or None
        :param client: (optional) if the activity was provided as a UUID, also provide a :class:`Client` object.
        :type client: `Client` or None
        :param kwargs: additional keyword arguments
        :type kwargs: dict or None
        :returns: None
        :raises IllegalArgumentError: if not provided one of :class:`Activity` or activity uuid and a `Client`
        """
        self._widgets = list(widgets)
        from pykechain.models import Activity
        from pykechain.models import Activity2
        if isinstance(activity, (Activity, Activity2)):
            self._activity_id = activity.id
            self._client = activity._client
        elif isinstance(activity, (text_type)) and client is not None:
            self._activity_id = activity
            self._client = client
        else:
            raise IllegalArgumentError("The `WidgetsManager` should be provided either an :class:`Activity` or "
                                       "an activity uuid and a `Client` to function properly.")

        self._iter = iter(self._widgets)

    def __repr__(self):  # pragma: no cover
        return "<pyke {} object {} widgets>".format(self.__class__.__name__, self.__len__())

    def __iter__(self):
        return self

    def __len__(self):
        return len(self._widgets)

    def __next__(self):
        # py3.4 and up style next
        return next(self._iter)

    next = __next__  # py2.7 alias

    def __getitem__(self, key):
        # type: (Any) -> Widget
        """Widget from the list of widgets based on index, uuid, title or ref."""
        found = None
        if isinstance(key, int):
            found = self._widgets[key]
        elif is_uuid(key):
            found = find(self._widgets, lambda p: key == p.id)
        elif isinstance(key, (string_types, text_type)):
            found = find(self._widgets, lambda p: key == p.title or key == p.ref)

        if found is not None:
            return found

        raise NotFoundError("Could not find widget with index, title, ref, or id {}".format(key))

    def create_widget(self, *args, **kwargs):
        """Create a widget inside an activity.

        If you want to associate models (and instances) in a single go, you may provide a list of `Property`
        (models) to the `readable_model_ids` or `writable_model_ids`.

        Alternatively you can use the alias, `inputs` and `outputs` which connect to respectively
        `readable_model_ids` and `writable_models_ids`.

        :param activity: activity objects to create the widget in.
        :type activity: :class:`Activity` or UUID
        :param widget_type: type of the widget, one of :class:`WidgetTypes`
        :type: string
        :param title: (optional) title of the widget
        :type title: str or None
        :param meta: meta dictionary of the widget.
        :type meta: dict
        :param order: (optional) order in the activity of the widget.
        :type order: int or None
        :param parent: (optional) parent of the widget for Multicolumn and Multirow widget.
        :type parent: :class:`Widget` or UUID
        :param readable_models: (optional) list of property model ids to be configured as readable (alias = inputs)
        :type readable_models: list of properties or list of property id's
        :param writable_models: (optional) list of property model ids to be configured as writable (alias = outputs)
        :type writable_models: list of properties or list of property id's
        :param kwargs: (optional) additional keyword=value arguments to create widget
        :type kwargs: dict or None
        :return: the created subclass of :class:`Widget`
        :rtype: :class:`Widget`
        :raises IllegalArgumentError: when an illegal argument is send.
        :raises APIError: when an API Error occurs.
        """
        widget = self._client.create_widget(*args, activity=self._activity_id, **kwargs)

        if kwargs.get('order') is None:
            self._widgets.append(widget)
        else:
            self.insert(kwargs.get('order'), widget)
        return widget

    def add_super_grid_widget(self, part_model, parent_instance=None, custom_title=False, new_instance=True,
                              edit=True, clone=True, export=True, delete=False, incomplete_rows=True,
                              emphasize_new_instance=True, emphasize_edit=False, emphasize_clone=False,
                              emphasize_delete=False, sort_property=None, sort_direction=SortTable.ASCENDING,
                              readable_models=None, writable_models=None, all_readable=False, all_writable=False,
                              **kwargs):
        """
        Add a KE-chain superGrid (e.g. basic table widget) to the customization.
        The widget will be saved to KE-chain.
        :param readable_models: List of `Property` models or `Property` UUIDs to be configured in the widget as readable
        :type readable_models: list
        :param writable_models: List of `Property` models or `Property` UUIDs to be configured in the widget as writable
        :type writable_models: list
        :param all_readable: Selects all the `Properties` of part_model and configures them as readable in the widget
        :type all_readable: bool
        :param all_writable: Selects all the `Properties` of part_model and configures them as writable in the widget
        :type all_writable: bool
        :param emphasize_new_instance: Emphasize the New instance button (default True)
        :type emphasize_new_instance: bool
        :param emphasize_edit: Emphasize the Edit button (default False)
        :type emphasize_edit: bool
        :param emphasize_clone: Emphasize the Clone button (default False)
        :type emphasize_clone: bool
        :param emphasize_delete: Emphasize the Delete button (default False)
        :type emphasize_delete: bool
        :param new_instance: Show or hide the New instance button (default False). You need to provide a
            `parent_instance` in order for this to work.
        :type new_instance: bool
        :param incomplete_rows: Show or hide the Incomplete Rows filter button (default True)
        :type incomplete_rows: bool
        :param export: Show or hide the Export Grid button (default True)
        :type export: bool
        :param edit: Show or hide the Edit button (default True)
        :type edit: bool
        :param clone: Show or hide the Clone button (default True)
        :type clone: bool
        :param delete: Show or hide the Delete button (default False)
        :type delete: bool
        :param part_model: The part model based on which all instances will be shown.
        :type parent_instance: :class:`Part` or UUID
        :param parent_instance: The parent part instance for which the instances will be shown or to which new
            instances will be added.
        :type parent_instance: :class:`Part` or UUID
        :param custom_height: The height of the supergrid in pixels
        :type custom_height: int or None
        :param custom_title: A custom title for the supergrid::
            * False (default): Part instance name
            * String value: Custom title
            * None: No title
        :type custom_title: bool or basestring or None
        :param sort_property: The property model on which the part instances are being sorted on
        :type sort_property: :class:`Property` or UUID
        :param sort_direction: The direction on which the values of property instances are being sorted on:
            * ASC (default): Sort in ascending order
            * DESC: Sort in descending order
        :type sort_direction: basestring (see :class:`enums.SortTable`)
        :raises IllegalArgumentError: When unknown or illegal arguments are passed.
        """
        # Check whether the part_model is uuid type or class `Part`
        part_model = _retrieve_object(ke_chain_object=part_model, client=self._client)  # type: Part2
        parent_instance = _retrieve_object_id(ke_chain_object=parent_instance)  # type: Part2
        sort_property_id = _retrieve_object_id(ke_chain_object=sort_property)  # type: text_type

        meta = _initiate_meta(kwargs=kwargs, activity_id=self._activity_id)
        meta.update({
            # grid
            "partModelId": part_model.id,
            # columns
            "sortedColumn": sort_property_id if sort_property_id else None,
            "sortDirection": sort_direction,
            # buttons
            "addButtonVisible": new_instance if parent_instance else False,
            "editButtonVisible": edit,
            "deleteButtonVisible": delete,
            "cloneButtonVisible": clone,
            "downloadButtonVisible": export,
            "incompleteRowsVisible": incomplete_rows,
            "primaryAddUiValue": emphasize_new_instance,
            "primaryEditUiValue": emphasize_edit,
            "primaryCloneUiValue": emphasize_clone,
            "primaryDeleteUiValue": emphasize_delete,
        })

        if parent_instance:
            meta['parentInstanceId'] = parent_instance

        if all_readable and all_writable:
            raise IllegalArgumentError('Properties can be either writable or readable, but not both')

        if all_readable and not readable_models:
            readable_models = part_model.properties
        if all_writable and not writable_models:
            writable_models = part_model.properties

        meta, title = _set_title(meta, custom_title, default_title=part_model.name)

        widget = self.create_widget(
            widget_type=WidgetTypes.SUPERGRID,
            title=title,
            meta=meta,
            order=kwargs.get("order"),
            parent=kwargs.get("parent_widget"),
            readable_models=readable_models,
            writable_models=writable_models
        )
        return widget

    def add_filteredgrid_widget(self, part_model, parent_instance=None, custom_title=False, new_instance=True,
                                edit=True, clone=True, export=True, delete=False, incomplete_rows=True,
                                emphasize_new_instance=True, emphasize_edit=False, emphasize_clone=False,
                                emphasize_delete=False, sort_property=None, sort_direction=SortTable.ASCENDING,
                                collapse_filters=False, page_size=25, readable_models=None, writable_models=None,
                                all_readable=False, all_writable=False,
                                **kwargs):
        """
        Add a KE-chain superGrid (e.g. basic table widget) to the customization.
        The widget will be saved to KE-chain.
        :param readable_models: List of `Property` models or `Property` UUIDs to be configured in the widget as readable
        :type readable_models: list
        :param writable_models: List of `Property` models or `Property` UUIDs to be configured in the widget as writable
        :type writable_models: list
        :param all_readable: Selects all the `Properties` of part_model and configures them as readable in the widget
        :type all_readable: bool
        :param all_writable: Selects all the `Properties` of part_model and configures them as writable in the widget
        :type all_writable: bool
        :param emphasize_new_instance: Emphasize the New instance button (default True)
        :type emphasize_new_instance: bool
        :param emphasize_edit: Emphasize the Edit button (default False)
        :type emphasize_edit: bool
        :param emphasize_clone: Emphasize the Clone button (default False)
        :type emphasize_clone: bool
        :param emphasize_delete: Emphasize the Delete button (default False)
        :type emphasize_delete: bool
        :param new_instance: Show or hide the New instance button (default False). You need to provide a
            `parent_instance` in order for this to work.
        :type new_instance: bool
        :param incomplete_rows: Show or hide the Incomplete Rows filter button (default True)
        :type incomplete_rows: bool
        :param export: Show or hide the Export Grid button (default True)
        :type export: bool
        :param edit: Show or hide the Edit button (default True)
        :type edit: bool
        :param clone: Show or hide the Clone button (default True)
        :type clone: bool
        :param delete: Show or hide the Delete button (default False)
        :type delete: bool
        :param collapse_filters: Hide or show the filters pane (default False)
        :type collapse_filters: bool
        :param page_size: Number of parts that will be shown per page in the grid.
        :type page_size: int
        :param part_model: The part model based on which all instances will be shown.
        :type parent_instance: :class:`Part` or UUID
        :param parent_instance: The parent part instance for which the instances will be shown or to which new
            instances will be added.
        :type parent_instance: :class:`Part` or UUID
        :param custom_height: The height of the supergrid in pixels
        :type custom_height: int or None
        :param custom_title: A custom title for the supergrid::
            * False (default): Part instance name
            * String value: Custom title
            * None: No title
        :type custom_title: bool or basestring or None
        :param sort_property: The property model on which the part instances are being sorted on
        :type sort_property: :class:`Property` or UUID
        :param sort_direction: The direction on which the values of property instances are being sorted on:
            * ASC (default): Sort in ascending order
            * DESC: Sort in descending order
        :type sort_direction: basestring (see :class:`enums.SortTable`)
        :raises IllegalArgumentError: When unknown or illegal arguments are passed.
        """
        # Check whether the part_model is uuid type or class `Part`
        part_model = _retrieve_object(ke_chain_object=part_model, client=self._client)  # type: Part2
        parent_instance_id = _retrieve_object_id(ke_chain_object=parent_instance)  # type: text_type
        sort_property_id = _retrieve_object_id(ke_chain_object=sort_property)  # type: text_type

        meta = _initiate_meta(kwargs=kwargs, activity_id=self._activity_id)
        meta.update({
            # grid
            "partModelId": part_model.id,
            # columns
            "sortedColumn": sort_property_id if sort_property_id else None,
            "sortDirection": sort_direction,
            "showCollapseFiltersValue": "Collapsed" if collapse_filters else "Expanded",  # compatibility
            "collapseFilters": collapse_filters,
            "customPageSize": page_size,
            # buttons
            "addButtonVisible": new_instance if parent_instance_id else False,
            "editButtonVisible": edit,
            "deleteButtonVisible": delete,
            "cloneButtonVisible": clone,
            "downloadButtonVisible": export,
            "incompleteRowsVisible": incomplete_rows,
            "primaryAddUiValue": emphasize_new_instance,
            "primaryEditUiValue": emphasize_edit,
            "primaryCloneUiValue": emphasize_clone,
            "primaryDeleteUiValue": emphasize_delete,
        })

        if parent_instance_id:
            meta['parentInstanceId'] = parent_instance_id

        if all_readable and all_writable:
            raise IllegalArgumentError('Properties can be either writable or readable, but not both')

        if all_readable and not readable_models:
            readable_models = part_model.properties
        if all_writable and not writable_models:
            writable_models = part_model.properties

        meta, title = _set_title(meta, custom_title, default_title=part_model.name)

        widget = self.create_widget(
            widget_type=WidgetTypes.FILTEREDGRID,
            title=title,
            meta=meta,
            order=kwargs.get("order"),
            parent=kwargs.get("parent_widget"),
            readable_models=readable_models,
            writable_models=writable_models
        )
        return widget

    def add_attachmentviewer_widget(self, attachment_property, custom_title=False, height=None,
                                    alignment=None,
                                    readable_models=None, parent_widget=None, **kwargs):
        # type: (Union[Text, Property2], Optional[Text, bool], Optional[int], Optional[Text], Optional[Iterable], Optional[Widget,Text], **Any) -> Widget  # noqa

        attachment_property = _retrieve_object(attachment_property, client=self._client)  # type: Property2
        meta = _initiate_meta(kwargs, activity_id=self._activity_id)

        meta.update({
            "propertyInstanceId": attachment_property.id,
        })

        meta, title = _set_title(meta, custom_title, default_title=attachment_property.name)
        widget = self.create_widget(
            widget_type=WidgetTypes.ATTACHMENTVIEWER,
            meta=meta,
            title=title,
            order=kwargs.get("order"),
            parent=kwargs.get("parent_widget"),
            readable_models=[attachment_property.id],
        )

        return widget

    def add_tasknavigationbar_widget(self, activities,
                                     alignment=NavigationBarAlignment.CENTER,
                                     parent_widget=None, **kwargs):
        # type: (Union[Iterable[Dict]], Optional[Text], Optional[Widget,Text], **Any) -> Widget  # noqa
        """
        Add a KE-chain Navigation Bar (e.g. navigation bar widget) to the activity.

        The widget will be saved to KE-chain.

        :param activities: List of activities. Each activity must be a Python dict(), with the following keys:
            * customText: A custom text for each button in the attachment viewer widget: None (default): Task name;
            a String value: Custom text
            * emphasized: bool which determines if the button should stand-out or not - default(False)
            * activityId: class `Activity` or UUID
            * isDisabled: (optional) to disable the navbar button
        :type activities: list of dict
        :param alignment: The alignment of the buttons inside navigation bar. One of :class:`NavigationBarAlignment`
            * center (default): Center aligned
            * start: left aligned
        :type alignment: basestring (see :class:`enums.NavigationBarAlignment`)
        :raises IllegalArgumentError: When unknown or illegal arguments are passed.
        """
        set_of_expected_keys = {'activityId', 'customText', 'emphasized', 'emphasize', 'isDisabled'}
        for activity_dict in activities:
            if set(activity_dict.keys()).issubset(set_of_expected_keys) and 'activityId' in set_of_expected_keys:
                # Check whether the activityId is class `Activity` or UUID
                activity = activity_dict['activityId']
                from pykechain.models import Activity2
                if isinstance(activity, Activity2):
                    activity_dict['activityId'] = activity.id
                elif isinstance(activity, text_type) and is_uuid(activity):
                    pass
                else:
                    raise IllegalArgumentError("When using the add_navigation_bar_widget, activityId must be an "
                                               "Activity or Activity id. Type is: {}".format(type(activity)))
                if 'customText' not in activity_dict or not activity_dict['customText']:
                    activity_dict['customText'] = ''
                if 'emphasized' not in activity_dict:
                    activity_dict['emphasized'] = False
                if 'emphasize' in activity_dict:  # emphasize is to be moved to emphasized
                    # TODO: pending deprecation in version 3.4.0
                    warnings.warn(PendingDeprecationWarning, "The `emphasize` key in the navbar button will be "
                                                             "deprecated in pykechain 3.4.0")
                    activity_dict['emphasized'] = activity_dict.pop('emphasize')

            else:
                raise IllegalArgumentError("Found unexpected key in activities. Only keys allowed are: {}".
                                           format(set_of_expected_keys))

        meta = _initiate_meta(kwargs, activity_id=self._activity_id)
        meta['taskButtons'] = activities
        # removed meta items that are not allowed but added by the _initiate meta
        _ = meta.pop('showHeightValue'), meta.pop('customHeight'), meta.pop('collapsed'), meta.pop('collapsible'), \
            meta.pop('noPadding'), meta.pop('noBackground')

        # TODO: pending deprecation in version 3.4.0
        if alignment and alignment is NavigationBarAlignment.START:
            warnings.warn(PendingDeprecationWarning, "In KE-chain 3 we use the LEFT alignment, instead of START "
                                                     "alignment of the task navigationbar widgets. Will be autocorrected"
                                                     "to LEFT alignment for now. Please correct your code as this is "
                                                     "pending deprecation at version 3.4.0")
            alignment = NavigationBarAlignment.LEFT

        if alignment and alignment not in (NavigationBarAlignment.CENTER, NavigationBarAlignment.LEFT):
            raise IllegalArgumentError("`alignment` should be one of '{}'".format(NavigationBarAlignment.values()))
        elif alignment:
            meta['alignment'] = alignment

        widget = self.create_widget(
            widget_type=WidgetTypes.TASKNAVIGATIONBAR,
            meta=meta,
            parent=parent_widget,
            **kwargs
        )

        return widget

    def add_propertygrid_widget(self, part_instance, custom_title=False, max_height=None, show_headers=True,
                                show_columns=None, parent_widget=None, readable_models=None, writable_models=None,
                                all_readable=False, **kwargs):
        # type: (Union[Property2, Text], Optional[Text, bool], Optional[int], bool, Optional[Iterable], Optional[Text, Widget], Optional[Iterable], Optional[Iterable], bool, **Any ) -> Widget
        """
        Add a KE-chain Property Grid widget to the customization.

        The widget will be saved to KE-chain.
        :param part_instance: The part instance on which the property grid will be based
        :type part_instance: :class:`Part` or UUID
        :param max_height: The max height of the property grid in pixels
        :type max_height: int or None
        :param custom_title: A custom title for the property grid::
            * False (default): Part instance name
            * String value: Custom title
            * None: No title
        :type custom_title: bool or basestring or None
        :param show_headers: Show or hide the headers in the grid (default True)
        :type show_headers: bool
        :param show_columns: Columns to be hidden or shown (default to 'unit' and 'description')
        :type show_columns: list
        :param parent_widget: (optional) parent of the widget for Multicolumn and Multirow widget.
        :type parent_widget: Widget or str or None
        :param readable_models: list of property model ids to be configured as readable (alias = inputs)
        :type readable_models: list of properties or list of property id's
        :param writable_models: list of property model ids to be configured as writable (alias = outputs)
        :type writable_models: list of properties or list of property id's
        :param all_readable: (optional) boolean indicating if all properties should automatically be configured as
        readable (if True) or writable (if False).
        :type all_readable: bool
        :param kwargs: (optional) additional keyword=value arguments to create widget
        :type kwargs: dict or None
        :raises IllegalArgumentError: When unknown or illegal arguments are passed.
        """
        # Check whether the part_model is uuid type or class `Part`
        part_instance = _retrieve_object(part_instance, client=self._client)  # type: Part2

        if not show_columns:
            show_columns = list()

        # Set the display_columns for the config
        possible_columns = [ShowColumnTypes.DESCRIPTION, ShowColumnTypes.UNIT]
        display_columns = dict()

        for possible_column in possible_columns:
            if possible_column in show_columns:
                display_columns[possible_column] = True
            else:
                display_columns[possible_column] = False

        meta = _initiate_meta(kwargs=kwargs, activity_id=self._activity_id)
        meta.update({
            "customHeight": max_height if max_height else None,
            "partInstanceId": part_instance.id,
            "showColumns": show_columns,
            "showHeaders": show_headers,
            "showHeightValue": "Custom max height" if max_height else "Auto",
        })

        meta, title = _set_title(meta, custom_title, default_title=part_instance.name)

        if all_readable and not readable_models:
            readable_models = part_instance.model().properties
        elif not writable_models:
            writable_models = part_instance.model().properties

        widget = self.create_widget(
            widget_type=WidgetTypes.PROPERTYGRID,
            title=title,
            meta=meta,
            parent=parent_widget,
            order=kwargs.get("order"),
            readable_models=readable_models,
            writable_models=writable_models
        )
        return widget

    def add_service_widget(self, service, custom_title=False, custom_button_text=False, emphasize_run=True,
                           download_log=False, parent_widget=None, **kwargs):
        """
        Add a KE-chain Service (e.g. script widget) to the widget manager.

        The widget will be saved to KE-chain.

        :param service: The Service to which the button will be coupled and will be ran when the button is pressed.
        :type service: :class:`Service` or UUID
        :param custom_title: A custom title for the script widget
            * False (default): Script name
            * String value: Custom title
            * None: No title
        :type custom_title: bool or basestring or None
        :param custom_button_text: A custom text for the button linked to the script
            * False (default): Script name
            * String value: Custom title
            * None: No title
        :type custom_button_text: bool or basestring or None
        :param emphasize_run: Emphasize the run button (default True)
        :type emphasize_run: bool
        :param download_log: Include the possibility of downloading the log inside the activity (default False)
        :type download_log: bool
        :param download_log: Include the log message inside the activity (default True)
        :type download_log: bool
        :param parent_widget: (optional) parent of the widget for Multicolumn and Multirow widget.
        :type parent_widget: Widget or str or None
        :raises IllegalArgumentError: When unknown or illegal arguments are passed.
        """
        meta = _initiate_meta(kwargs=kwargs, activity_id=self._activity_id)

        # Check whether the script is uuid type or class `Service`
        from pykechain.models import Service
        if isinstance(service, Service):
            script_id = service.id
        elif isinstance(service, (string_types, text_type)) and is_uuid(service):
            script_id = service
            service = self._client.service(id=script_id)
        else:
            raise IllegalArgumentError("When using the add_script_widget, script must be a Service or Service id. "
                                       "Type is: {}".format(type(service)))

        # Add custom button text
        if custom_button_text is False:
            show_button_value = "Default"
            button_text = service.name
        elif custom_button_text is None:
            show_button_value = "No text"
            button_text = ''
        else:
            show_button_value = "Custom text"
            button_text = str(custom_button_text)

        meta.update({
            'showButtonValue': show_button_value,
            'customText': button_text,
            'serviceId': script_id,
            'emphasizeButton': emphasize_run,
            'showDownloadLog': download_log,
            'showLog': kwargs.get('show_log', True)
        })

        meta, title = _set_title(meta, custom_title, default_title=service.name)

        widget = self.create_widget(
            widget_type=WidgetTypes.SERVICE,
            title=title,
            meta=meta,
            parent=parent_widget,
            order=kwargs.get("order")
        )

        return widget

    def add_text_widget(self, *args, **kwargs):
        """Add a KE-chain HTML widget to the activity."""
        warnings.warn(PendingDeprecationWarning, "The `add_text_widget()` method will be deprecated in favor of "
                                                 "`add_html_widget` in version 3.4.0")
        return self.add_html_widget(*args, **kwargs)

    def add_html_widget(self, html, custom_title=None, **kwargs):
        """
        Add a KE-chain HTML widget to the widget manager.
        The widget will be saved to KE-chain.
        :param html: The text that will be shown by the widget.
        :type html: basestring or None
        :param custom_title: A custom title for the text panel::
            * None (default): No title
            * String value: Custom title
        :type custom_title: basestring or None
        :param collapsible: A boolean to decide whether the panel is collapsible or not (default True)
        :type collapsible: bool
        :param collapsed: A boolean to decide whether the panel is collapsed or not (default False)
        :type collapsible: bool
        :raises IllegalArgumentError: When unknown or illegal arguments are passed.
        """
        if not isinstance(html, text_type):
            raise IllegalArgumentError("Text injected in the HTML widget must be string. Type is: {}".
                                       format(type(html)))

        meta = _initiate_meta(kwargs, activity_id=self._activity_id)

        meta, title = _set_title(meta, custom_title, default_title=None)
        meta["htmlContent"] = html

        widget = self.create_widget(
            widget_type=WidgetTypes.HTML,
            title=title,
            meta=meta,
            order=kwargs.get("order"),
            parent=kwargs.get("parent_widget")
        )
        return widget



    #
    # Widget manager methods
    #

    def insert(self, index, widget):
        # type: (int, Widget) -> None
        """
        Insert a widget at index n, shifting the rest of the list to the right.

        if widget order is `[w0,w1,w2]` and inserting `w4` at index 2 (before Widget1);
        the list will be `[w0,w4,w1,w2]`

        :param index: integer (position) starting from 1 at first position in which the widget is inserted
        :type index: int
        :param widget: Widget object to insert
        :type widget: Widget
        :return: None
        :raises IndexError: The index is out of range
        :raises APIError: The list of widgets could not be updated
        """
        if index < 0 or index > self.__len__():
            raise IndexError("The index is out of range. "
                             "The list of widgets is '{}' widget(s) long.".format(self.__len__()))

        # TODO check if this works
        bisect.insort(self._widgets, widget)

        # bulk update the order of the widgets:
        fvalues = [dict(id=w.id, order=index) for index, w in enumerate(self._widgets)]

        from pykechain.client import API_EXTRA_PARAMS
        response = self._client._request("PUT", self._client._build_url('widgets'),
                                         params=API_EXTRA_PARAMS['widgets'],
                                         data=fvalues)

        if response.status_code != requests.codes.ok:
            raise APIError("Could not update the order of the widgets: {}: {}".format(str(response), response.content))

        widgets_response = response.json().get('results')
        for widget, updated_response in self._widgets, widgets_response:
            widget.refresh(json=updated_response)

    def delete_all_widgets(self):
        """Delete all widgets.

        :return: None
        :raises ApiError: When the deletion of the widgets was not succesfull
        """
        widget_ids = [dict(id=w.id) for w in self.__iter__()]
        url = self._client._build_url('widgets_bulk_delete')
        response = self._client._request('DELETE', url, json=widget_ids)

        if response.status_code != requests.codes.no_content:
            raise APIError("Could not delete the widgets: {}: {}".format(str(response), response.content))

        self._widgets = []
