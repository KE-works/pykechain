import warnings
from typing import Iterable, Union, AnyStr, Optional, Text, Dict, List, Any

from pykechain.enums import SortTable, WidgetTypes, ShowColumnTypes, ScopeWidgetColumnTypes, \
    ProgressBarColors, PropertyType, CardWidgetImageValue, CardWidgetLinkValue, LinkTargets, ImageFitValue, \
    KEChainPages, CardWidgetKEChainPageLink, Alignment, ActivityType
from pykechain.exceptions import NotFoundError, IllegalArgumentError
from pykechain.models.input_checks import check_enum, check_text, check_base, check_type, check_list_of_text
from pykechain.models.widgets import Widget
from pykechain.models.widgets.helpers import _set_title, _initiate_meta, _retrieve_object, _retrieve_object_id, \
    _check_prefilters, _check_excluded_propmodels
from pykechain.utils import is_uuid, find, snakecase, is_url


class WidgetsManager(Iterable):
    """Manager for Widgets.

    This is the list of widgets. The widgets in the list are accessible directly using an index, uuid of the widget,
    widget title or widget 'ref'.
    """

    def __init__(self,
                 widgets: Iterable[Widget],
                 activity: Union['Activity2', AnyStr],
                 client: Optional['Client'] = None,
                 **kwargs) -> None:
        """Construct a Widget Manager from a list of widgets.

        You need to provide an :class:`Activity` to initiate the WidgetsManager. Alternatively you may provide both a
        activity uuid and a :class:`Client`.

        :param widgets: list of widgets.
        :type widgets: List[Widget]
        :param activity: an :class:`Activity` object or an activity UUID
        :type activity: basestring or None
        :param client: (O) if the activity was provided as a UUID, also provide a :class:`Client` object.
        :type client: `Client` or None
        :param kwargs: additional keyword arguments
        :type kwargs: dict or None
        :returns: None
        :raises IllegalArgumentError: if not provided one of :class:`Activity` or activity uuid and a `Client`
        """
        self._widgets = list(widgets)  # type: List[Widget]
        for widget in self._widgets:
            widget.manager = self
        from pykechain.models import Activity2
        from pykechain import Client
        if isinstance(activity, Activity2):
            self._activity_id = activity.id
            self._client = activity._client  # type: Client
        elif isinstance(activity, str) and client is not None:
            self._activity_id = activity
            self._client = client  # type: Client
        else:
            raise IllegalArgumentError("The `WidgetsManager` should be provided either an :class:`Activity` or "
                                       "an activity uuid and a `Client` to function properly.")

        self._iter = iter(self._widgets)

    def __repr__(self) -> Text:  # pragma: no cover
        return "<pyke {} object {} widgets>".format(self.__class__.__name__, self.__len__())

    def __iter__(self):
        return self

    def __len__(self) -> int:
        return len(self._widgets)

    def __next__(self) -> Widget:
        # py3.4 and up style next
        return next(self._iter)

    next = __next__  # py2.7 alias

    def __getitem__(self, key: Union[int, str, Widget]) -> Widget:
        """Widget from the list of widgets based on index, uuid, title or ref.

        :param key: index, uuid, title or ref of the widget to retrieve
        :type key: int or basestring
        :return: Retrieved widget
        :rtype: Widget
        :raises NotFoundError: when the widget could not be found
        """
        found = None
        if isinstance(key, Widget) and key in self._widgets:
            found = key
        elif isinstance(key, int):
            found = self._widgets[key]
        elif is_uuid(key):
            found = find(self._widgets, lambda p: key == p.id)
        elif isinstance(key, str):
            found = find(self._widgets, lambda p: key == p.title or key == p.ref)

        if found is not None:
            return found
        raise NotFoundError("Could not find widget with index, title, ref, or id '{}'".format(key))

    def __contains__(self, item: Widget) -> bool:
        return item in self._widgets

    def create_widgets(self, widgets: List[Dict]) -> List[Widget]:
        """
        Create widgets in bulk.

        :param widgets: list of dicts defining the configuration per widget.
        :type widgets: List[Dict]
        :returns list of widgets
        :rtype: List[Widget]
        """
        # Insert the current widget
        for widget in widgets:
            widget['activity'] = self._activity_id

        return self._client.create_widgets(widgets=widgets)

    def create_widget(self, *args, **kwargs) -> Widget:
        """Create a widget inside an activity.

        If you want to associate models (and instances) in a single go, you may provide a list of `Property`
        (models) to the `readable_model_ids` or `writable_model_ids`.

        Alternatively you can use the alias, `inputs` and `outputs` which connect to respectively
        `readable_model_ids` and `writable_models_ids`.

        :param activity: activity objects to create the widget in.
        :type activity: :class:`Activity` or UUID
        :param widget_type: type of the widget, one of :class:`WidgetTypes`
        :type: string
        :param title: (O) title of the widget
        :type title: basestring or None
        :param meta: meta dictionary of the widget.
        :type meta: dict
        :param order: (O) order in the activity of the widget.
        :type order: int or None
        :param parent: (O) parent of the widget for Multicolumn and Multirow widget.
        :type parent: :class:`Widget` or UUID
        :param readable_models: (O) list of property model ids to be configured as readable (alias = inputs)
        :type readable_models: list of properties or list of property id's
        :param writable_models: (O) list of property model ids to be configured as writable (alias = outputs)
        :type writable_models: list of properties or list of property id's
        :param kwargs: additional keyword arguments to pass
        :return: newly created widget
        :rtype: Widget
        :raises IllegalArgumentError: when incorrect arguments are provided
        :raises APIError: When the widget could not be created.
        """
        if 'parent_widget' in kwargs:
            kwargs['parent'] = kwargs.pop('parent_widget')

        widget = self._client.create_widget(*args, activity=self._activity_id, **kwargs)

        if kwargs.get('order') is None:
            self._widgets.append(widget)
        else:
            self.insert(kwargs.get('order'), widget)
        return widget

    def create_configured_widget(
            self,
            part: 'Part2',
            all_readable: Optional[bool] = None,
            all_writable: Optional[bool] = None,
            readable_models: Optional[List[Union['AnyProperty', Text]]] = None,
            writable_models: Optional[List[Union['AnyProperty', Text]]] = None,
            **kwargs
    ) -> Widget:
        """
        Create a widget with configured properties.

        :param part: Part to retrieve the properties from if all_readable or all_writable is True.
        :type part: Part2
        :param all_readable: Selects all the `Properties` of part_model and configures them as readable in the widget
        :type all_readable: bool
        :param all_writable: Selects all the `Properties` of part_model and configures them as writable in the widget
        :type all_writable: bool
        :param readable_models: (O) list of property model ids to be configured as readable (alias = inputs)
        :type readable_models: list of properties or list of property id's
        :param writable_models: (O) list of property model ids to be configured as writable (alias = outputs)
        :type writable_models: list of properties or list of property id's
        :param kwargs: additional keyword arguments to pass
        :return: Widget
        """
        if all_readable and all_writable:
            raise IllegalArgumentError('Properties can be either writable or readable, but not both.')

        all_property_models = [p.model_id if p.model_id else p for p in part.properties]

        if all_readable and not readable_models:
            readable_models = all_property_models
        if all_writable and not writable_models:
            writable_models = all_property_models

        return self.create_widget(
            readable_models=readable_models,
            writable_models=writable_models,
            **kwargs)

    def add_supergrid_widget(self,
                             part_model: Union['Part2', Text],
                             parent_instance: Optional[Union['Part2', Text]] = None,
                             title: Optional[Union[type(None), Text, bool]] = False,
                             parent_widget: Optional[Union[Widget, Text]] = None,
                             new_instance: Optional[bool] = True,
                             edit: Optional[bool] = True,
                             clone: Optional[bool] = True,
                             export: Optional[bool] = True,
                             delete: Optional[bool] = False,
                             incomplete_rows: Optional[bool] = True,
                             emphasize_new_instance: Optional[bool] = True,
                             emphasize_edit: Optional[bool] = False,
                             emphasize_clone: Optional[bool] = False,
                             emphasize_delete: Optional[bool] = False,
                             sort_property: Optional[Union['AnyProperty', Text]] = None,
                             sort_direction: Optional[Union[SortTable, Text]] = SortTable.ASCENDING,
                             show_name_column: Optional[bool] = True,
                             show_images: Optional[bool] = False,
                             readable_models: Optional[List[Union['AnyProperty', Text]]] = None,
                             writable_models: Optional[List[Union['AnyProperty', Text]]] = None,
                             all_readable: Optional[bool] = False,
                             all_writable: Optional[bool] = False,
                             **kwargs) -> Widget:
        """
        Add a KE-chain superGrid (e.g. basic table widget) to the customization.

        The widget will be saved to KE-chain.

        :param part_model: The part model based on which all instances will be shown.
        :type part_model: :class:`Part` or UUID
        :param parent_instance: The parent part instance for which the instances will be shown or to which new
            instances will be added.
        :type parent_instance: :class:`Part` or UUID
        :param title: A custom title for the supergrid::
            * False (default): Part instance name
            * String value: Custom title
            * None: No title
        :type title: bool or basestring or None
        :param new_instance: Show or hide the New instance button (default False). You need to provide a
            `parent_instance` in order for this to work.
        :type new_instance: bool
        :param edit: Show or hide the Edit button (default True)
        :type edit: bool
        :param clone: Show or hide the Clone button (default True)
        :type clone: bool
        :param export: Show or hide the Export Grid button (default True)
        :type export: bool
        :param delete: Show or hide the Delete button (default False)
        :type delete: bool
        :param incomplete_rows: Show or hide the Incomplete Rows filter button (default True)
        :type incomplete_rows: bool
        :param emphasize_new_instance: Emphasize the New instance button (default True)
        :type emphasize_new_instance: bool
        :param emphasize_edit: Emphasize the Edit button (default False)
        :type emphasize_edit: bool
        :param emphasize_clone: Emphasize the Clone button (default False)
        :type emphasize_clone: bool
        :param emphasize_delete: Emphasize the Delete button (default False)
        :type emphasize_delete: bool
        :param sort_property: The property model on which the part instances are being sorted on
        :type sort_property: :class:`Property` or UUID
        :param sort_direction: The direction on which the values of property instances are being sorted on:
            * ASC (default): Sort in ascending order
            * DESC: Sort in descending order
        :type sort_direction: basestring (see :class:`enums.SortTable`)
        :param show_name_column: (O) show the column with part names
        :type show_name_column: bool
        :param show_images: (O) show the attachments in the grid as images, not as hyperlinks (default False).
        :type show_images: bool
        :param readable_models: List of `Property` models or `Property` UUIDs to be configured in the widget as readable
        :type readable_models: list
        :param writable_models: List of `Property` models or `Property` UUIDs to be configured in the widget as writable
        :type writable_models: list
        :param all_readable: Selects all the `Properties` of part_model and configures them as readable in the widget
        :type all_readable: bool
        :param all_writable: Selects all the `Properties` of part_model and configures them as writable in the widget
        :type all_writable: bool
        :param kwargs: additional keyword arguments to pass
        :return: newly created widget
        :rtype: Widget
        :raises IllegalArgumentError: when incorrect arguments are provided
        :raises APIError: When the widget could not be created.
        """
        # Check whether the part_model is uuid type or class `Part`
        part_model = _retrieve_object(obj=part_model, method=self._client.model)  # type: 'Part2'  # noqa
        parent_instance = _retrieve_object_id(obj=parent_instance)  # type: 'Part2'  # noqa
        sort_property_id = _retrieve_object_id(obj=sort_property)

        meta = _initiate_meta(kwargs=kwargs, activity=self._activity_id)
        meta.update({
            # grid
            "partModelId": part_model.id,
            # columns
            "sortedColumn": sort_property_id if sort_property_id else None,
            "sortDirection": sort_direction,
            "showNameColumn": show_name_column,
            "showImages": show_images,
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

        meta, title = _set_title(meta, title=title, default_title=part_model.name, **kwargs)

        widget = self.create_configured_widget(
            widget_type=WidgetTypes.SUPERGRID,
            title=title,
            meta=meta,
            parent=parent_widget,
            part=part_model,
            readable_models=readable_models,
            writable_models=writable_models,
            all_readable=all_readable,
            all_writable=all_writable,
            **kwargs
        )
        return widget

    def add_filteredgrid_widget(self,
                                part_model: Union['Part2', Text],
                                parent_instance: Optional[Union['Part2', Text]] = None,
                                title: Optional[Union[type(None), Text, bool]] = False,
                                parent_widget: Optional[Union[Widget, Text]] = None,
                                new_instance: Optional[bool] = True,
                                edit: Optional[bool] = True,
                                clone: Optional[bool] = True,
                                export: Optional[bool] = True,
                                delete: Optional[bool] = False,
                                incomplete_rows: Optional[bool] = True,
                                emphasize_new_instance: Optional[bool] = True,
                                emphasize_edit: Optional[bool] = False,
                                emphasize_clone: Optional[bool] = False,
                                emphasize_delete: Optional[bool] = False,
                                sort_property: Optional[Union['AnyProperty', Text]] = None,
                                sort_name: Optional[Union[bool, Text]] = False,
                                sort_direction: Optional[Union[SortTable, Text]] = SortTable.ASCENDING,
                                show_name_column: Optional[bool] = True,
                                show_images: Optional[bool] = False,
                                collapse_filters: Optional[bool] = False,
                                page_size: Optional[int] = 25,
                                readable_models: Optional[List[Union['AnyProperty', Text]]] = None,
                                writable_models: Optional[List[Union['AnyProperty', Text]]] = None,
                                all_readable: Optional[bool] = False,
                                all_writable: Optional[bool] = False,
                                excluded_propmodels: Optional[List[Union['AnyProperty', Text]]] = None,
                                prefilters: Optional[Dict] = None,
                                **kwargs) -> Widget:
        """
        Add a KE-chain superGrid (e.g. basic table widget) to the customization.

        The widget will be saved to KE-chain.

        :param part_model: The part model based on which all instances will be shown.
        :type part_model: :class:`Part` or UUID
        :param parent_instance: The parent part instance for which the instances will be shown or to which new
            instances will be added.
        :type parent_instance: :class:`Part` or UUID
        :param title: A custom title for the supergrid:
            * False (default): Part instance name
            * String value: Custom title
            * None: No title
        :type title: bool or basestring or None
        :param new_instance: Show or hide the New instance button (default False). You need to provide a
            `parent_instance` in order for this to work.
        :type new_instance: bool
        :param edit: Show or hide the Edit button (default True)
        :type edit: bool
        :param clone: Show or hide the Clone button (default True)
        :type clone: bool
        :param export: Show or hide the Export Grid button (default True)
        :type export: bool
        :param delete: Show or hide the Delete button (default False)
        :type delete: bool
        :param incomplete_rows: Show or hide the Incomplete Rows filter button (default True)
        :type incomplete_rows: bool
        :param emphasize_new_instance: Emphasize the New instance button (default True)
        :type emphasize_new_instance: bool
        :param emphasize_edit: Emphasize the Edit button (default False)
        :type emphasize_edit: bool
        :param emphasize_clone: Emphasize the Clone button (default False)
        :type emphasize_clone: bool
        :param emphasize_delete: Emphasize the Delete button (default False)
        :type emphasize_delete: bool
        :param sort_property: The property model on which the part instances are being sorted on
        :type sort_property: :class:`Property` or UUID
        :param sort_name: If set to True it will sort on name of the part. It is ignored if sort_property is None
        :type sort_name: bool
        :param sort_direction: The direction on which the values of property instances are being sorted on:
            * ASC (default): Sort in ascending order
            * DESC: Sort in descending order
        :type sort_direction: basestring (see :class:`enums.SortTable`)
        :param show_name_column: (O) show the column with part names
        :type show_name_column: bool
        :param show_images: (O) show the attachments in the grid as images, not as hyperlinks (default False).
        :type show_images: bool
        :param collapse_filters: Hide or show the filters pane (default False)
        :type collapse_filters: bool
        :param page_size: Number of parts that will be shown per page in the grid.
        :type page_size: int
        :param readable_models: List of `Property` models or `Property` UUIDs to be configured in the widget as readable
        :type readable_models: list
        :param writable_models: List of `Property` models or `Property` UUIDs to be configured in the widget as writable
        :type writable_models: list
        :param all_readable: Selects all the `Properties` of part_model and configures them as readable in the widget
        :type all_readable: bool
        :param all_writable: Selects all the `Properties` of part_model and configures them as writable in the widget
        :type all_writable: bool
        :param excluded_propmodels: (O) list of properties not shown in the filter pane
        :type excluded_propmodels: list
        :param prefilters: (O) default filters active in the grid, defined as a dict with the following fields:
            * property_models: list of Properties, defined as Property2 objects or UUIDs
            * values: the pre-filter value for each property to filter on
            * filters_type: the types of filters, either `le`, `ge`, `icontains` or `exact`
        :type prefilters: dict

        :param kwargs: additional keyword arguments to pass
        :return: newly created widget
        :rtype: Widget
        :raises IllegalArgumentError: when incorrect arguments are provided
        :raises APIError: When the widget could not be created.
        """
        # Check whether the part_model is uuid type or class `Part`
        part_model = _retrieve_object(obj=part_model, method=self._client.model)  # type: 'Part2'  # noqa
        parent_instance_id = _retrieve_object_id(obj=parent_instance)  # type: text_type
        sort_property_id = _retrieve_object_id(obj=sort_property)  # type: text_type
        if not sort_property_id and sort_name:
            sort_property_id = "name"
        meta = _initiate_meta(kwargs=kwargs, activity=self._activity_id)
        if prefilters:
            list_of_prefilters = _check_prefilters(part_model=part_model, prefilters=prefilters)
            prefilters = {'property_value': ','.join(list_of_prefilters) if list_of_prefilters else {}}
            meta['prefilters'] = prefilters
        if excluded_propmodels:
            excluded_propmodels = _check_excluded_propmodels(part_model=part_model,
                                                             property_models=excluded_propmodels)
            meta['propmodelsExcl'] = excluded_propmodels

        meta.update({
            # grid
            "partModelId": part_model.id,
            # columns
            "sortedColumn": sort_property_id if sort_property_id else None,
            "sortDirection": sort_direction,
            "showCollapseFiltersValue": "Collapsed" if collapse_filters else "Expanded",  # compatibility
            "collapseFilters": collapse_filters,
            "customPageSize": page_size,
            "showNameColumn": show_name_column,
            "showImages": show_images,
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

        meta, title = _set_title(meta, title=title, default_title=part_model.name, **kwargs)

        widget = self.create_configured_widget(
            widget_type=WidgetTypes.FILTEREDGRID,
            title=title,
            meta=meta,
            parent=parent_widget,
            part=part_model,
            readable_models=readable_models,
            writable_models=writable_models,
            all_readable=all_readable,
            all_writable=all_writable,
            **kwargs,
        )
        return widget

    def add_attachmentviewer_widget(self,
                                    attachment_property: Union[Text, 'AttachmentProperty2'],
                                    editable: Optional[bool] = False,
                                    title: Optional[Union[Text, bool]] = False,
                                    parent_widget: Optional[Union[Widget, Text]] = None,
                                    alignment: Optional[Alignment] = None,
                                    image_fit: Optional[Union[ImageFitValue, Text]] = ImageFitValue.CONTAIN,
                                    show_download_button: Optional[bool] = True,
                                    show_full_screen_button: Optional[bool] = True,
                                    **kwargs) -> Widget:
        """
        Add a KE-chain Attachment widget widget manager.

        The widget will be saved to KE-chain.

        :param attachment_property: KE-chain Attachment property to display
        :type attachment_property: AttachmentProperty
        :param editable: Whether the attachment can be added, edited or deleted (default: False)
        :type editable: bool
        :param title: A custom title for the script widget
            * False (default): Script name
            * String value: Custom title
            * None: No title
        :type title: bool or basestring or None
        :param alignment: horizontal alignment of the previewed attachment (Alignment enum class)
        :type alignment: Alignment
        :param image_fit: (O) enumeration to address the image_fit (defaults to 'contain', otherwise 'cover')
        :type image_fit: basestring or None
        :param show_download_button: (O) whether a user can download the attached figure (defaults to True)
        :type show_download_button: bool
        :param show_full_screen_button: (O) whether the figure can be expanded to fit the full screen (defaults to True)
        :type show_full_screen_button: bool
        :param kwargs: additional keyword arguments to pass
        :return: newly created widget
        :rtype: Widget
        :raises IllegalArgumentError: when incorrect arguments are provided
        :raises APIError: When the widget could not be created.
        """
        attachment_property = _retrieve_object(attachment_property,
                                               method=self._client.property)  # type: 'Property2'
        meta = _initiate_meta(kwargs, activity=self._activity_id)

        meta.update({
            "propertyInstanceId": attachment_property.id,
            "alignment": check_enum(alignment, Alignment, 'alignment'),
            "imageFit": check_enum(image_fit, ImageFitValue, 'image_fit'),
            "showDownloadButton": check_type(show_download_button, bool, 'show_download_button'),
            "showFullscreenImageButton": check_type(show_full_screen_button, bool, 'show_full_screen_button'),
        })

        for deprecated_kw in ['widget_type', 'readable_models']:
            if deprecated_kw in kwargs:
                kwargs.pop(deprecated_kw)
                warnings.warn('Argument "{}" is no longer supported as input to `add_attachment_viewer`.'.format(
                    deprecated_kw), Warning)

        meta, title = _set_title(meta, title=title, default_title=attachment_property.name, **kwargs)

        if check_type(editable, bool, 'editable'):
            kwargs.update({'writable_models': [attachment_property.model_id]})
        else:
            kwargs.update({'readable_models': [attachment_property.model_id]})

        widget = self.create_widget(
            widget_type=WidgetTypes.ATTACHMENTVIEWER,
            meta=meta,
            title=title,
            parent=parent_widget,
            **kwargs,
        )

        return widget

    def add_tasknavigationbar_widget(self,
                                     activities: Union[Iterable[Dict]],
                                     alignment: Optional[Text] = Alignment.CENTER,
                                     parent_widget: Optional[Union[Widget, Text]] = None,
                                     **kwargs) -> Widget:
        """
        Add a KE-chain Navigation Bar (e.g. navigation bar widget) to the activity.

        The widget will be saved to KE-chain.

        :param activities: List of activities. Each activity must be a Python dict(), with the following keys:
            * customText: A custom text for each button in the attachment viewer widget: None (default): Task name;
            a String value: Custom text
            * emphasized: bool which determines if the button should stand-out or not - default(False)
            * activityId: class `Activity` or UUID
            * isDisabled: (O) to disable the navbar button
            * link: str URL to external web page
        :type activities: list of dict
        :param alignment: The alignment of the buttons inside navigation bar. One of :class:`Alignment`
            * left: Left aligned
            * center (default): Center aligned
            * right: Right aligned
        :type alignment: basestring (see :class:`enums.NavigationBarAlignment`)
        :param kwargs: additional keyword arguments to pass
        :return: newly created widget
        :rtype: Widget
        :raises IllegalArgumentError: when incorrect arguments are provided
        :raises APIError: When the widget could not be created.
        """
        from pykechain.models import Activity2

        set_of_expected_keys = {'activityId', 'customText', 'emphasized', 'emphasize', 'isDisabled', 'link'}
        task_buttons = list()
        for nr, input_dict in enumerate(activities):
            if not set(input_dict.keys()).issubset(set_of_expected_keys):
                raise IllegalArgumentError("Found unexpected key in activities. Only keys allowed are: {}".
                                           format(set_of_expected_keys))
            button_dict = dict()
            task_buttons.append(button_dict)

            if 'activityId' in input_dict:
                # Check whether the activityId is class `Activity` or UUID
                activity = input_dict['activityId']
                if isinstance(activity, Activity2):
                    button_dict['activityId'] = activity.id
                elif isinstance(activity, str) and is_uuid(activity):
                    button_dict['activityId'] = activity
                else:
                    raise IllegalArgumentError("When using the add_navigation_bar_widget, activityId must be an "
                                               "Activity or Activity id. Type is: {}".format(type(activity)))
            elif 'link' in input_dict:
                if not is_url(input_dict['link']):
                    raise IllegalArgumentError("The link should be an URL, got '{}'".format(input_dict['link']))
                button_dict['link'] = input_dict['link']
            else:
                raise IllegalArgumentError("Each button must have key 'activityId' or 'link'. "
                                           "Button {} has neither.".format(nr + 1))

            if 'customText' not in input_dict or not input_dict['customText']:
                button_dict['customText'] = ''
            else:
                button_dict['customText'] = str(input_dict['customText'])

            button_dict['emphasize'] = input_dict.get('emphasize', False)

            button_dict['isDisabled'] = input_dict.get('isDisabled', False)

        meta = _initiate_meta(kwargs, activity=self._activity_id, ignores=('showHeightValue',))
        meta['taskButtons'] = task_buttons
        meta['alignment'] = check_enum(alignment, Alignment, 'alignment')

        widget = self.create_widget(
            widget_type=WidgetTypes.TASKNAVIGATIONBAR,
            meta=meta,
            parent=parent_widget,
            **kwargs
        )

        return widget

    def add_propertygrid_widget(self,
                                part_instance: Union['Part2', Text],
                                title: Optional[Union[Text, bool]] = False,
                                max_height: Optional[int] = None,
                                show_headers: Optional[bool] = True,
                                show_columns: Optional[Iterable] = None,
                                parent_widget: Optional[Union[Text, Widget]] = None,
                                readable_models: Optional[Iterable] = None,
                                writable_models: Optional[Iterable] = None,
                                all_readable: Optional[bool] = False,
                                all_writable: Optional[bool] = False,
                                **kwargs) -> Widget:
        """
        Add a KE-chain Property Grid widget to the customization.

        The widget will be saved to KE-chain.
        :param part_instance: The part instance on which the property grid will be based
        :type part_instance: :class:`Part` or UUID
        :param max_height: The max height of the property grid in pixels
        :type max_height: int or None
        :param title: A custom title for the property grid::
            * False (default): Part instance name
            * String value: Custom title
            * None: No title
        :type title: bool or basestring or None
        :param show_headers: Show or hide the headers in the grid (default True)
        :type show_headers: bool
        :param show_columns: Columns to be hidden or shown (default to 'unit' and 'description')
        :type show_columns: list
        :param parent_widget: (O) parent of the widget for Multicolumn and Multirow widget.
        :type parent_widget: Widget or basestring or None
        :param readable_models: list of property model ids to be configured as readable (alias = inputs)
        :type readable_models: list of properties or list of property id's
        :param writable_models: list of property model ids to be configured as writable (alias = outputs)
        :type writable_models: list of properties or list of property id's
        :param all_readable: (O) boolean indicating if all properties should automatically be configured as
        readable (if True) or writable (if False).
        :type all_readable: bool
        :param all_writable: (O) boolean indicating if all properties should automatically be configured as
        writable (if True) or writable (if False).
        :type all_writable: bool
        :param kwargs: additional keyword arguments to pass
        :return: newly created widget
        :rtype: Widget
        :raises IllegalArgumentError: when incorrect arguments are provided
        :raises APIError: When the widget could not be created.
        """
        # Check whether the part_model is uuid type or class `Part`
        part_instance = _retrieve_object(part_instance, method=self._client.part)  # type: 'Part2'  # noqa: F821

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

        meta = _initiate_meta(kwargs=kwargs, activity=self._activity_id)
        meta.update({
            "customHeight": max_height if max_height else None,
            "partInstanceId": part_instance.id,
            "showColumns": show_columns,
            "showHeaders": show_headers,
        })

        meta, title = _set_title(meta, title=title, default_title=part_instance.name, **kwargs)

        widget = self.create_configured_widget(
            widget_type=WidgetTypes.PROPERTYGRID,
            title=title,
            meta=meta,
            parent=parent_widget,
            part=part_instance,
            readable_models=readable_models,
            writable_models=writable_models,
            all_readable=all_readable,
            all_writable=all_writable,
            **kwargs
        )
        return widget

    def add_service_widget(self,
                           service: 'Service',
                           title: Optional[Union[type(None), bool, Text]] = False,
                           custom_button_text: Optional[Text] = False,
                           emphasize_run: Optional[bool] = True,
                           download_log: Optional[bool] = False,
                           show_log: Optional[bool] = True,
                           parent_widget: Optional[Union[Widget, Text]] = None,
                           **kwargs) -> Widget:
        """
        Add a KE-chain Service (e.g. script widget) to the widget manager.

        The widget will be saved to KE-chain.

        :param service: The Service to which the button will be coupled and will be ran when the button is pressed.
        :type service: :class:`Service` or UUID
        :param title: A custom title for the script widget
            * False (default): Script name
            * String value: Custom title
            * None: No title
        :type title: bool or basestring or None
        :param custom_button_text: A custom text for the button linked to the script
            * False (default): Script name
            * String value: Custom title
            * None: No title
        :type custom_button_text: bool or basestring or None
        :param emphasize_run: Emphasize the run button (default True)
        :type emphasize_run: bool
        :param download_log: Include the possibility of downloading the log inside the activity (default False)
        :type download_log: bool
        :param show_log: Include the log message inside the activity (default True)
        :type show_log: bool
        :param parent_widget: (O) parent of the widget for Multicolumn and Multirow widget.
        :type parent_widget: Widget or basestring or None
        :param kwargs: additional keyword arguments to pass
        :return: newly created widget
        :rtype: Widget
        :raises IllegalArgumentError: when incorrect arguments are provided
        :raises APIError: When the widget could not be created.
        """
        # Check whether the script is uuid type or class `Service`
        service = _retrieve_object(obj=service, method=self._client.service)  # type: 'Service'  # noqa

        meta = _initiate_meta(kwargs=kwargs, activity=self._activity_id)

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

        from pykechain.models import Service
        service_id = check_base(service, Service, 'service', method=self._client.service)

        meta.update({
            'showButtonValue': show_button_value,
            'customText': button_text,
            'serviceId': service_id,
            'emphasizeButton': emphasize_run,
            'showDownloadLog': check_type(download_log, bool, 'download_log'),
            'showLog': True if download_log else check_type(show_log, bool, 'show_log'),
        })

        meta, title = _set_title(meta, title=title, default_title=service.name, **kwargs)

        widget = self.create_widget(
            widget_type=WidgetTypes.SERVICE,
            title=title,
            meta=meta,
            parent=parent_widget,
            **kwargs,
        )

        return widget

    def add_html_widget(self,
                        html: Optional[Text],
                        title: Optional[Union[type(None), bool, Text]] = None,
                        parent_widget: Optional[Union[Widget, Text]] = None,
                        **kwargs) -> Widget:
        """
        Add a KE-chain HTML widget to the widget manager.

        The widget will be saved to KE-chain.

        :param html: The text that will be shown by the widget.
        :type html: basestring or None
        :param title: A custom title for the text panel::
            * None (default): No title
            * String value: Custom title
        :type title: basestring or None
        :param parent_widget: (O) parent of the widget for Multicolumn and Multirow widget.
        :type parent_widget: Widget or basestring or None
        :param kwargs: additional keyword arguments to pass
        :return: newly created widget
        :rtype: Widget
        :raises IllegalArgumentError: when incorrect arguments are provided
        :raises APIError: When the widget could not be created.
        """
        check_text(html, 'html')

        meta = _initiate_meta(kwargs, activity=self._activity_id)
        meta, title = _set_title(meta, title=title, default_title=WidgetTypes.HTML, **kwargs)

        meta["htmlContent"] = html

        widget = self.create_widget(
            widget_type=WidgetTypes.HTML,
            title=title,
            meta=meta,
            parent=parent_widget,
            **kwargs,
        )
        return widget

    def add_notebook_widget(self,
                            notebook: 'Service',
                            title: Optional[Union[type(None), bool, Text]] = False,
                            parent_widget: Optional[Union[Widget, Text]] = None,
                            **kwargs) -> Widget:
        """
        Add a KE-chain Notebook (e.g. notebook widget) to the WidgetManager.

        The widget will be saved to KE-chain.

        :param notebook: The Notebook to which the button will be coupled and will start when the button is pressed.
        :type notebook: :class:`Service` or UUID
        :param title: A custom title for the notebook widget
            * False (default): Notebook name
            * String value: Custom title
            * None: No title
        :type title: bool or basestring or None
        :param parent_widget: (O) parent of the widget for Multicolumn and Multirow widget.
        :type parent_widget: Widget or basestring or None
        :param kwargs: additional keyword arguments to pass
        :return: newly created widget
        :rtype: Widget
        :raises IllegalArgumentError: when incorrect arguments are provided
        :raises APIError: When the widget could not be created.

        """
        from pykechain.models import Service
        if isinstance(notebook, Service):
            notebook_id = notebook.id
        elif isinstance(notebook, str) and is_uuid(notebook):
            notebook_id = notebook
            notebook = self._client.service(id=notebook_id)
        else:
            raise IllegalArgumentError("When using the add_notebook_widget, notebook must be a Service or Service id. "
                                       "Type is: {}".format(type(notebook)))

        meta = _initiate_meta(kwargs=kwargs, activity=self._activity_id)
        meta, title = _set_title(meta, title=title, default_title=notebook.name, **kwargs)

        meta.update({
            'serviceId': notebook_id
        })

        widget = self.create_widget(
            widget_type=WidgetTypes.NOTEBOOK,
            title=title,
            meta=meta,
            parent=parent_widget,
            **kwargs,
        )

        return widget

    def add_metapanel_widget(self,
                             show_all: Optional[bool] = True,
                             show_due_date: Optional[bool] = False,
                             show_start_date: Optional[bool] = False,
                             show_title: Optional[bool] = False,
                             show_status: Optional[bool] = False,
                             show_progress: Optional[bool] = False,
                             show_assignees: Optional[bool] = False,
                             show_breadcrumbs: Optional[bool] = False,
                             show_menu: Optional[bool] = False,
                             show_download_pdf: Optional[bool] = False,
                             show_progressbar: Optional[bool] = False,
                             progress_bar: Optional[Dict] = None,
                             breadcrumb_root: Optional['Activity2'] = None,
                             **kwargs) -> Widget:
        """
        Add a KE-chain Metapanel to the WidgetManager.

        The widget will be saved to KE-chain.

        :param show_all: Show all elements of the metapanel (defaults to True). If True other arguments are ignored.
        :type show_all: bool
        :param show_due_date: show Due date
        :type show_due_date: bool
        :param show_start_date: show Start date
        :type show_start_date: bool
        :param show_title: Show Title of the activity
        :type show_title: bool
        :param show_status: Show status
        :type show_status: bool
        :param show_progress: Show progress. If True, the progressbar is not shown.
        :type show_progress: bool
        :param show_assignees: show Assignees
        :type show_assignees: bool
        :param show_breadcrumbs: show Breadcrumbs
        :type show_breadcrumbs: bool
        :param show_download_pdf: Show the Download PDF button
        :type show_download_pdf: bool
        :param show_menu: show Menu
        :type show_menu: bool
        :param show_progressbar: Show the progress bar. Shown when progress is not True.
        :type show_progressbar: bool
        :param progress_bar: Progress bar custom settings. Allowed dictionary items `colorNoProgress, showProgressText,
        showProgressText, customHeight, colorInProgress, colorCompleted, colorInProgressBackground`
        :type progress_bar: dict or None
        :param breadcrumb_root: Activity2 object or UUID to specify the breadcrumb root
        :type breadcrumb_root: Activity2
        :param kwargs: additional keyword arguments to pass
        :return: newly created widget
        :rtype: Widget
        :raises IllegalArgumentError: when incorrect arguments are provided
        :raises APIError: When the widget could not be created.
        """
        meta = _initiate_meta(kwargs, activity=self._activity_id)

        if show_all:
            meta['showAll'] = True
        else:
            from pykechain.models import Activity2
            meta.update(dict(
                showAll=False,
                showDueDate=show_due_date,
                showStartDate=show_start_date,
                showTitle=show_title,
                showStatus=show_status,
                showMenuDownloadPDF=show_download_pdf,
                showAssignees=show_assignees,
                showBreadCrumb=show_breadcrumbs,
                # if show_download_pdf = Tue -> showMenu = True by default
                showMenu=show_menu or show_download_pdf,
                # if the progress = True -> bar = False. Also when the bar is set to True,
                # if progress=False and Bar=True, the bar is True
                # if progress=False and Bar=False, both are False
                showProgress=show_progress and not show_progressbar or show_progress,
                showProgressBar=show_progressbar and not show_progress,
                breadcrumbAncestor=check_base(breadcrumb_root, Activity2, 'breadcrumb_root') or None,
            ))
        if progress_bar:
            meta.update(dict(
                progressBarSettings=dict(
                    colorNoProgress=progress_bar.get('colorNoProgress', ProgressBarColors.DEFAULT_NO_PROGRESS),
                    showProgressText=progress_bar.get('showProgressText', True),
                    customHeight=progress_bar.get('customHeight', 25),
                    colorInProgress=progress_bar.get('colorInProgress', ProgressBarColors.DEFAULT_IN_PROGRESS),
                    colorCompleted=progress_bar.get('colorCompleted', ProgressBarColors.DEFAULT_COMPLETED),
                    colorInProgressBackground=progress_bar.get('colorInProgressBackground',
                                                               ProgressBarColors.DEFAULT_IN_PROGRESS_BACKGROUND),
                )
            ))
        widget = self.create_widget(
            widget_type=WidgetTypes.METAPANEL,
            title=kwargs.pop('title', WidgetTypes.METAPANEL),
            meta=meta,
            **kwargs
        )
        return widget

    def add_progress_widget(self,
                            height: Optional[int] = 25,
                            color_no_progress: Optional[
                                Union[str, ProgressBarColors]] = ProgressBarColors.DEFAULT_NO_PROGRESS,
                            color_completed: Optional[
                                Union[str, ProgressBarColors]] = ProgressBarColors.DEFAULT_COMPLETED,
                            color_in_progress: Optional[
                                Union[str, ProgressBarColors]] = ProgressBarColors.DEFAULT_IN_PROGRESS,
                            color_in_progress_background: Optional[
                                Union[str, ProgressBarColors]] = ProgressBarColors.DEFAULT_IN_PROGRESS_BACKGROUND,
                            show_progress_text: Optional[bool] = True,
                            **kwargs) -> Widget:
        """
        Add a KE-chain progress bar widget to the WidgetManager.

        The widget will be saved to KE-chain.

        :param height: height of the progress bar, counted in pixels
        :param color_no_progress: color option for when the progress bar is empty
        :param color_completed: color option for when the progress bar is fully completed
        :param color_in_progress: color option for the filled part of the progress bar
        :param color_in_progress_background: color option for the empty part of the progress bar
        :param show_progress_text: visualize the progress percentage
        :param kwargs: additional keyword arguments to pass
        :return: newly created widget
        :rtype Widget
        """
        meta = _initiate_meta(kwargs, activity=self._activity_id)

        meta.update(dict(
            colorNoProgress=color_no_progress,
            showProgressText=show_progress_text,
            customHeight=height,
            colorInProgress=color_in_progress,
            colorCompleted=color_completed,
            colorInProgressBackground=color_in_progress_background
        ))
        widget = self.create_widget(
            widget_type=WidgetTypes.PROGRESS,
            meta=meta,
            **kwargs
        )
        return widget

    def add_multicolumn_widget(self,
                               title: Optional[Text] = None,
                               **kwargs) -> Widget:
        """
        Add a KE-chain Multi Column widget to the WidgetManager.

        The widget will be saved to KE-chain.

        :param title: A custom title for the multi column widget
            * False: Widget id
            * String value: Custom title
            * None (default): No title
        :type title: bool or basestring or None
        :param kwargs: additional keyword arguments to pass
        :return: newly created widget
        :rtype: Widget
        :raises IllegalArgumentError: when incorrect arguments are provided
        :raises APIError: When the widget could not be created.
        """
        meta = _initiate_meta(kwargs=kwargs, activity=self._activity_id)
        meta, title = _set_title(meta, title=title, default_title=WidgetTypes.MULTICOLUMN, **kwargs)

        widget = self.create_widget(
            widget_type=WidgetTypes.MULTICOLUMN,
            title=title,
            meta=meta,
            parent=None,
            **kwargs,
        )
        return widget

    def add_scope_widget(self,
                         team: Union['Team', Text] = None,
                         title: Optional[Text] = None,
                         add: Optional[bool] = True,
                         edit: Optional[bool] = True,
                         clone: Optional[bool] = True,
                         delete: Optional[bool] = True,
                         emphasize_add: Optional[bool] = True,
                         emphasize_edit: Optional[bool] = False,
                         emphasize_clone: Optional[bool] = False,
                         emphasize_delete: Optional[bool] = False,
                         show_columns: Optional[Iterable[Text]] = None,
                         show_all_columns: Optional[bool] = True,
                         page_size: Optional[int] = 25,
                         tags: Optional[Iterable[Text]] = None,
                         sorted_column: Optional[Text] = ScopeWidgetColumnTypes.PROJECT_NAME,
                         sorted_direction: Optional[SortTable] = SortTable.ASCENDING,
                         parent_widget: Optional[Union[Widget, Text]] = None,
                         active_filter: Optional[bool] = True,
                         search_filter: Optional[bool] = True,
                         **kwargs) -> Widget:
        """
        Add a KE-chain Scope widget to the Widgetmanager and the activity.

        The widget will be saved in KE-chain.

        :param team: Team to limit the list of scopes to. Providing this is not obligated but highly preferred.
        :type team: :class:`Team` or basestring
        :param title:A custom title for the multi column widget
            * False: Widget id
            * String value: Custom title
            * None (default): No title
        :type title: bool or basestring or None
        :param add: (O) Show or hide the Add button (default True)
        :type add: bool
        :param clone: (O) Show or hide the Clone button (default True)
        :type clone: bool
        :param edit: (O) Show or hide the Edit button (default True)
        :type edit: bool
        :param delete: (O) Show or hide the Delete button (default True)
        :type delete: bool
        :param emphasize_add: (O) Emphasize the Add button (default True)
        :type emphasize_add: bool
        :param emphasize_clone: (O) Emphasize the Clone button (default False)
        :type emphasize_clone: bool
        :param emphasize_edit: (O) Emphasize the Edit button (default False)
        :type emphasize_edit: bool
        :param emphasize_delete: (O) Emphasize the Delete button (default False)
        :type emphasize_delete: bool
        :param show_columns: (O) list of column headers to show. One of `ScopeWidgetColumnTypes`.
        :type show_columns: list of basestring
        :param show_all_columns: boolean to show all columns (defaults to True). If True, will override `show_columns`
        :type show_all_columns: bool
        :param page_size: number of scopes to show per page (defaults to 25)
        :type page_size: int
        :param tags: (O) list of scope tags to filter the Scopes on
        :type tags: list of basestring
        :param sorted_column: column name to sort on. (defaults to project name column). One of `ScopeWidgetColumnTypes`
        :type sorted_column: basestring
        :param sorted_direction: The direction on which the values of property instances are being sorted on:
            * ASC (default): Sort in ascending order
            * DESC: Sort in descending order
        :type sorted_direction: basestring
        :param parent_widget: (O) parent of the widget for Multicolumn and Multirow widget.
        :type parent_widget: Widget or basestring or None
        :param active_filter: (O) whether to show the active-scopes filter, defaults to True
        :type active_filter: bool
        :param search_filter: (O) whether to show the search filter, defaults to True
        :type search_filter: bool
        :param kwargs: additional keyword arguments to pass
        :return: newly created widget
        :rtype: Widget
        :raises IllegalArgumentError: when incorrect arguments are provided
        :raises APIError: When the widget could not be created.
        """
        meta = _initiate_meta(kwargs, activity=self._activity_id)
        meta, title = _set_title(meta, title=title, default_title=WidgetTypes.SCOPE, **kwargs)

        check_type(show_all_columns, bool, 'show_all_columns')

        if not show_all_columns and show_columns:
            if not isinstance(show_columns, (list, tuple)):
                raise IllegalArgumentError('`show_columns` must be a list or tuple, "{}" is not.'.format(show_columns))
            options = set(ScopeWidgetColumnTypes.values())
            if not all(sc in options for sc in show_columns):
                raise IllegalArgumentError("`show_columns` must consist out of ScopeWidgetColumnTypes options.")
            meta['showColumns'] = [snakecase(c) for c in show_columns]

        if not isinstance(page_size, int) or page_size < 1:
            raise IllegalArgumentError('`page_size` must be a positive integer, "{}" is not.'.format(page_size))

        if team:
            meta['teamId'] = _retrieve_object_id(team)

        for button_setting in [
            add, edit, delete, clone, emphasize_add, emphasize_clone, emphasize_edit, emphasize_delete,
        ]:
            check_type(button_setting, bool, 'buttons')

        meta.update({
            'sortedColumn': snakecase(check_enum(sorted_column, ScopeWidgetColumnTypes, 'sorted_column')),
            'sortDirection': check_enum(sorted_direction, SortTable, 'sorted_direction'),
            'activeFilterVisible': check_type(active_filter, bool, 'active_filter'),
            'searchFilterVisible': check_type(search_filter, bool, 'search_filter'),
            "addButtonVisible": add,
            "editButtonVisible": edit,
            "deleteButtonVisible": delete,
            "cloneButtonVisible": clone,
            "primaryAddUiValue": emphasize_add,
            "primaryEditUiValue": emphasize_edit,
            "primaryCloneUiValue": emphasize_clone,
            "primaryDeleteUiValue": emphasize_delete,
            "customPageSize": page_size,
            "tags": check_list_of_text(tags, 'tags', True) or [],
        })

        widget = self.create_widget(
            widget_type=WidgetTypes.SCOPE,
            title=title,
            meta=meta,
            parent=parent_widget,
            **kwargs
        )
        return widget

    def add_signature_widget(self,
                             attachment_property: 'AttachmentProperty2',
                             title: Optional[Union[bool, Text]] = False,
                             parent_widget: Optional[Union[Widget, Text]] = None,
                             custom_button_text: Optional[Union[bool, Text]] = False,
                             custom_undo_button_text: Optional[Union[bool, Text]] = False,
                             **kwargs) -> Widget:
        """
        Add a KE-chain Signature widget to the Widgetmanager and the activity.

        The widget will be saved in KE-chain.

        :param attachment_property: KE-chain Attachment property to display
        :type attachment_property: AttachmentProperty
        :param title: A custom title for the script widget
            * False (default): Script name
            * String value: Custom title
            * None: No title
        :type title: bool or basestring or None
        :param custom_button_text: Custom text for 'Add signature' button
        :type custom_button_text: bool or basestring
        :param custom_undo_button_text: Custom text for 'Remove signature' button
        :type custom_undo_button_text: bool or basestring
        :param kwargs: additional keyword arguments to pass
        :return: newly created widget
        :rtype: Widget
        :raises IllegalArgumentError: when incorrect arguments are provided
        :raises APIError: When the widget could not be created.
        """
        attachment_property = _retrieve_object(attachment_property,
                                               method=self._client.property)  # type: 'AttachmentProperty2'  # noqa
        meta = _initiate_meta(kwargs, activity=self._activity_id)
        meta, title = _set_title(meta, title=title, default_title=attachment_property.name, **kwargs)

        # Add custom button text
        if not custom_button_text:
            show_button_value = "Default"
            button_text = ''
        else:
            show_button_value = "Custom text"
            button_text = str(custom_button_text)

        # Add custom undo button text
        if not custom_undo_button_text:
            show_undo_button_value = "Default"
            undo_button_text = ''
        else:
            show_undo_button_value = "Custom text"
            undo_button_text = str(custom_undo_button_text)

        meta.update({
            "propertyInstanceId": attachment_property.id,
            "showUndoButtonValue": show_undo_button_value,
            "customUndoText": undo_button_text,
            "customText": button_text,
            "showButtonValue": show_button_value
        })

        widget = self.create_widget(
            widget_type=WidgetTypes.SIGNATURE,
            meta=meta,
            title=title,
            parent=parent_widget,
            readable_models=[attachment_property.model_id],
            **kwargs,
        )
        return widget

    def add_card_widget(self,
                        image: Optional['AttachmentProperty2'] = None,
                        title: Optional[Union[type(None), Text, bool]] = None,
                        parent_widget: Optional[Union[Widget, Text]] = None,
                        description: Optional[Union[Text, bool]] = None,
                        link: Optional[Union[type(None), Text, bool, KEChainPages]] = None,
                        link_value: Optional[CardWidgetLinkValue] = None,
                        link_target: Optional[Union[Text, LinkTargets]] = LinkTargets.SAME_TAB,
                        image_fit: Optional[Union[ImageFitValue, Text]] = ImageFitValue.CONTAIN,
                        **kwargs) -> Widget:
        """
        Add a KE-chain Card widget to the WidgetManager and the activity.

        The widget will be saved in KE-chain.

        :param image: AttachmentProperty2 providing the source of the image shown in the card widget.
        :param title: A custom title for the card widget
            * False (default): Card name
            * String value: Custom title
            * None: No title
        :param description: Custom text shown below the image in the card widget
            * False (default): Card name
            * String value: Custom title
            * None: No title
        :param link: Where the card widget refers to. This can be one of the following:
            * None (default): no link
            * task: another KE-chain task, provided as an Activity2 object or its UUID
            * String value: URL to a webpage
            * KE-chain page: built-in KE-chain page of the current scope
        :param link_value: Overwrite the default link value (obtained from the type of the link)
        :type link_value: CardWidgetLinkValue
        :param link_target: how the link is opened, one of the values of CardWidgetLinkTarget enum.
        :type link_target: CardWidgetLinkTarget
        :param image_fit: how the image on the card widget is displayed
        :type image_fit: ImageFitValue
        :return: Card Widget
        """
        meta = _initiate_meta(kwargs, activity=self._activity_id)
        meta, title = _set_title(meta, title=title, default_title=WidgetTypes.CARD, **kwargs)

        # Process the description
        if description is False or description is None:
            show_description_value = "No description"
            description = ""
        elif isinstance(description, str):
            show_description_value = "Custom description"
        else:
            raise IllegalArgumentError("When using the add_card_widget, 'description' must be 'text_type' or None or "
                                       "False. Type is: {}".format(type(description)))

        meta.update({
            "showDescriptionValue": show_description_value,
            "customDescription": description
        })

        # Process the image it is linked to
        from pykechain.models import Property2
        if isinstance(image, Property2) and image.type == PropertyType.ATTACHMENT_VALUE:
            meta.update({
                'customImage': "/api/v3/properties/{}/preview".format(image.id),
                'showImageValue': CardWidgetImageValue.CUSTOM_IMAGE
            })
        elif image is None:
            meta.update({
                'customImage': None,
                'showImageValue': CardWidgetImageValue.NO_IMAGE
            })
        else:
            raise IllegalArgumentError("When using the add_card_widget, 'image' must be a Property or None. Type "
                                       "is: {}".format(type(image)))

        from pykechain.models import Activity2
        if isinstance(link, Activity2):
            if link.activity_type == ActivityType.TASK:
                default_link_value = CardWidgetLinkValue.TASK_LINK
            else:
                default_link_value = CardWidgetLinkValue.TREE_VIEW

            meta.update({
                'customLink': link.id,
                'showLinkValue': default_link_value,
            })
        elif isinstance(link, str) and is_uuid(link):
            meta.update({
                'customLink': link,
                'showLinkValue': CardWidgetLinkValue.TASK_LINK,
            })
        elif link is None or link is False:
            meta.update({
                'customLink': None,
                'showLinkValue': CardWidgetLinkValue.NO_LINK,
            })
        elif link in KEChainPages.values():
            meta.update({
                'customLink': "",
                'showLinkValue': CardWidgetKEChainPageLink[link],
            })
        else:
            meta.update({
                'customLink': link,
                'showLinkValue': CardWidgetLinkValue.EXTERNAL_LINK,
            })

        if link_value is not None:
            meta.update({
                'showLinkValue': check_enum(link_value, CardWidgetLinkValue, 'link_value'),
            })

        meta['linkTarget'] = check_enum(link_target, LinkTargets, 'link_target')
        meta['imageFit'] = check_enum(image_fit, ImageFitValue, 'image_fit')

        widget = self.create_widget(
            widget_type=WidgetTypes.CARD,
            meta=meta,
            title=title,
            parent=parent_widget,
            **kwargs,
        )
        return widget

    #
    # Widget manager methods
    #

    def insert(self, index: int, widget: Widget) -> None:
        """
        Insert a widget at index n, shifting the rest of the list to the right.

        if widget order is `[w0,w1,w2]` and inserting `w3` at index 1 (before Widget1);
        the list will be `[w0,w3,w1,w2]`

        :param index: integer (position) starting from 0 at first position in which the widget is inserted
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

        if widget in self._widgets:
            self._widgets.remove(widget)
        self._widgets.insert(index, widget)

        widgets = [dict(id=w.id, order=index) for index, w in enumerate(self._widgets)]

        self._widgets = self._client.update_widgets(widgets=widgets)

    def delete_widget(self, key: Any) -> bool:
        """
        Delete a widget in the task.

        :param key: index, uuid, title or ref of the widget to delete, or the widget itself.
        :type key: Widget, int or basestring
        :return: True if the widget is deleted successfully
        :raises APIError: if the widget could not be deleted
        :raises NotFoundError: if the WidgetsManager (activity) has no such widget
        """
        widget = self[key]
        self._client.delete_widget(widget=widget)
        self._widgets.remove(widget)
        return True

    def delete_all_widgets(self) -> None:
        """
        Delete all widgets in the activity.

        :return: None
        :raises ApiError: When the deletion of the widgets was not successful
        """
        self._client.delete_widgets(list(self))
        self._widgets = []
        return None
