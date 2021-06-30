import warnings
from typing import (
    Iterable,
    Union,
    Optional,
    Text,
    Dict,
    List,
    Any,
)

from pykechain.enums import (
    SortTable,
    WidgetTypes,
    ShowColumnTypes,
    ScopeWidgetColumnTypes,
    ProgressBarColors,
    CardWidgetLinkValue,
    LinkTargets,
    ImageFitValue,
    KEChainPages,
    Alignment,
    ActivityStatus,
    ActivityType,
    ActivityClassification,
)
from pykechain.exceptions import NotFoundError, IllegalArgumentError
from pykechain.models.input_checks import (
    check_enum,
    check_text,
    check_base,
    check_type,
    check_list_of_text,
)
from pykechain.models.value_filter import PropertyValueFilter
from pykechain.models.widgets import Widget
from pykechain.models.widgets.enums import (
    DashboardWidgetSourceScopes,
    DashboardWidgetShowTasks,
    DashboardWidgetShowScopes,
    MetaWidget,
    AssociatedObjectId,
    TasksAssignmentFilterTypes,
    TasksWidgetColumns,
)
from pykechain.models.widgets.helpers import (
    _set_title,
    _initiate_meta,
    _retrieve_object,
    _retrieve_object_id,
    _check_prefilters,
    _check_excluded_propmodels,
    _set_description,
    _set_link,
    _set_image,
    _set_button_text,
    TITLE_TYPING,
)
from pykechain.utils import is_uuid, find, snakecase, is_url


class WidgetsManager(Iterable):
    """Manager for Widgets.

    This is the list of widgets. The widgets in the list are accessible directly using an index, uuid of the widget,
    widget title or widget 'ref'.
    """

    def __init__(self,
                 widgets: Iterable[Widget],
                 activity: 'Activity',
                 **kwargs) -> None:
        """Construct a Widget Manager from a list of widgets.

        You need to provide an :class:`Activity` to initiate the WidgetsManager. Alternatively you may provide both a
        activity uuid and a :class:`Client`.

        :param widgets: list of widgets.
        :type widgets: List[Widget]
        :param activity: an :class:`Activity` object
        :type activity: Activity
        :param kwargs: additional keyword arguments
        :type kwargs: dict or None
        :returns: None
        :raises IllegalArgumentError: if not provided one of :class:`Activity` or activity uuid and a `Client`
        """
        self._widgets: List[Widget] = list(widgets)
        for widget in self._widgets:
            widget.manager = self

        from pykechain.models import Activity
        from pykechain import Client

        if not isinstance(activity, Activity):
            raise IllegalArgumentError(
                "The `WidgetsManager` should be provided a :class:`Activity` to function properly.")

        self.activity: Activity = activity
        self._activity_id = activity.id
        self._client: Client = activity._client

    def __repr__(self) -> Text:  # pragma: no cover
        return "<pyke {} object {} widgets>".format(self.__class__.__name__, self.__len__())

    def __iter__(self):
        return iter(self._widgets)

    def __len__(self) -> int:
        return len(self._widgets)

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
            widget["activity"] = self.activity

        new_widgets = self._client.create_widgets(widgets=widgets)
        self._widgets.extend(new_widgets)
        self._widgets.sort(key=lambda w: w.order)

        return new_widgets

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
        if "parent_widget" in kwargs:
            kwargs["parent"] = kwargs.pop("parent_widget")

        widget = self._client.create_widget(*args, activity=self.activity, **kwargs)

        if kwargs.get(MetaWidget.ORDER) is None:
            self._widgets.append(widget)
        else:
            self.insert(kwargs.get(MetaWidget.ORDER), widget)
        return widget

    def create_configured_widget(
            self,
            part: 'Part',
            all_readable: Optional[bool] = None,
            all_writable: Optional[bool] = None,
            readable_models: Optional[List[Union['AnyProperty', Text]]] = None,
            writable_models: Optional[List[Union['AnyProperty', Text]]] = None,
            **kwargs
    ) -> Widget:
        """
        Create a widget with configured properties.

        :param part: Part to retrieve the properties from if all_readable or all_writable is True.
        :type part: Part
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
            raise IllegalArgumentError("Properties can be either writable or readable, but not both.")

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
                             part_model: Union['Part', Text],
                             parent_instance: Optional[Union['Part', Text]] = None,
                             title: TITLE_TYPING = False,
                             parent_widget: Optional[Union[Widget, Text]] = None,
                             new_instance: Optional[bool] = True,
                             edit: Optional[bool] = True,
                             clone: Optional[bool] = True,
                             export: Optional[bool] = True,
                             upload: Optional[bool] = True,
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
        :param upload: Show or hide the Import Grid button (default True)
        :type upload: bool
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
        part_model: 'Part' = _retrieve_object(obj=part_model, method=self._client.model)  # noqa
        parent_instance: 'Part' = _retrieve_object_id(obj=parent_instance)  # noqa
        sort_property_id = _retrieve_object_id(obj=sort_property)

        meta = _initiate_meta(kwargs=kwargs, activity=self.activity)
        meta.update({
            # grid
            AssociatedObjectId.PART_MODEL_ID: part_model.id,
            # columns
            MetaWidget.SORTED_COLUMN: sort_property_id if sort_property_id else None,
            MetaWidget.SORTED_DIRECTION: sort_direction,
            MetaWidget.SHOW_NAME_COLUMN: show_name_column,
            MetaWidget.SHOW_IMAGES: show_images,
            # buttons
            MetaWidget.VISIBLE_ADD_BUTTON: new_instance if parent_instance else False,
            MetaWidget.VISIBLE_EDIT_BUTTON: edit,
            MetaWidget.VISIBLE_DELETE_BUTTON: delete,
            MetaWidget.VISIBLE_CLONE_BUTTON: clone,
            MetaWidget.VISIBLE_DOWNLOAD_BUTTON: export,
            MetaWidget.VISIBLE_UPLOAD_BUTTON: upload,
            MetaWidget.VISIBLE_INCOMPLETE_ROWS: incomplete_rows,
            MetaWidget.EMPHASIZE_ADD_BUTTON: emphasize_new_instance,
            MetaWidget.EMPHASIZE_EDIT_BUTTON: emphasize_edit,
            MetaWidget.EMPHASIZE_CLONE_BUTTON: emphasize_clone,
            MetaWidget.EMPHASIZE_DELETE_BUTTON: emphasize_delete,
        })

        if parent_instance:
            meta[AssociatedObjectId.PARENT_INSTANCE_ID] = parent_instance

        meta, title = _set_title(meta, title=title, **kwargs)

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

    def add_filteredgrid_widget(
            self,
            part_model: Union['Part', Text],
            parent_instance: Optional[Union['Part', Text]] = None,
            title: TITLE_TYPING = False,
            parent_widget: Optional[Union[Widget, Text]] = None,
            new_instance: Optional[bool] = True,
            edit: Optional[bool] = True,
            clone: Optional[bool] = True,
            export: Optional[bool] = True,
            upload: Optional[bool] = True,
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
            prefilters: Optional[Union[List[PropertyValueFilter], Dict]] = None,
            **kwargs
    ) -> Widget:
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
        :param upload: Show or hide the Import Grid button (default True)
        :type upload: bool
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
        :param collapse_filters: Boolean to collapses the filters pane, or fully hide if None. (default = False)
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
        :param prefilters: (O) default filters active in the grid.
            Defined as either a list of PropertyValueFilter objects or a dict with the following fields:
            * property_models: list of Properties, defined as Property objects or UUIDs
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
        part_model: 'Part' = _retrieve_object(obj=part_model, method=self._client.model)  # noqa
        parent_instance_id: text_type = _retrieve_object_id(obj=parent_instance)
        sort_property_id: text_type = _retrieve_object_id(obj=sort_property)
        if not sort_property_id and sort_name:
            sort_property_id = MetaWidget.NAME
        meta = _initiate_meta(kwargs=kwargs, activity=self.activity)
        if prefilters:
            list_of_prefilters = _check_prefilters(part_model=part_model, prefilters=prefilters)
            prefilters = {MetaWidget.PROPERTY_VALUE_PREFILTER: ",".join([pf.format() for pf in list_of_prefilters])}
            meta[MetaWidget.PREFILTERS] = prefilters
        if excluded_propmodels:
            excluded_propmodels = _check_excluded_propmodels(part_model=part_model,
                                                             property_models=excluded_propmodels)
            meta[MetaWidget.EXCLUDED_PROPERTY_MODELS] = excluded_propmodels

        meta.update({
            # grid
            AssociatedObjectId.PART_MODEL_ID: part_model.id,
            # columns
            MetaWidget.SORTED_COLUMN: sort_property_id if sort_property_id else None,
            MetaWidget.SORTED_DIRECTION: sort_direction,
            MetaWidget.COLLAPSE_FILTERS: collapse_filters,
            MetaWidget.SHOW_FILTERS: collapse_filters is not None,
            MetaWidget.CUSTOM_PAGE_SIZE: page_size,
            MetaWidget.SHOW_NAME_COLUMN: show_name_column,
            MetaWidget.SHOW_IMAGES: show_images,
            # buttons
            MetaWidget.VISIBLE_ADD_BUTTON: new_instance if parent_instance_id else False,
            MetaWidget.VISIBLE_EDIT_BUTTON: edit,
            MetaWidget.VISIBLE_DELETE_BUTTON: delete,
            MetaWidget.VISIBLE_CLONE_BUTTON: clone,
            MetaWidget.VISIBLE_DOWNLOAD_BUTTON: export,
            MetaWidget.VISIBLE_UPLOAD_BUTTON: upload,
            MetaWidget.VISIBLE_INCOMPLETE_ROWS: incomplete_rows,
            MetaWidget.EMPHASIZE_ADD_BUTTON: emphasize_new_instance,
            MetaWidget.EMPHASIZE_EDIT_BUTTON: emphasize_edit,
            MetaWidget.EMPHASIZE_CLONE_BUTTON: emphasize_clone,
            MetaWidget.EMPHASIZE_DELETE_BUTTON: emphasize_delete,
        })

        if parent_instance_id:
            meta[AssociatedObjectId.PARENT_INSTANCE_ID] = parent_instance_id

        meta, title = _set_title(meta, title=title, **kwargs)

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
            **kwargs
        )
        return widget

    def add_attachmentviewer_widget(self,
                                    attachment_property: Union[Text, 'AttachmentProperty'],
                                    editable: Optional[bool] = False,
                                    title: TITLE_TYPING = False,
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
            * False (default): Property name
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
        attachment_property: 'Property' = _retrieve_object(attachment_property,
                                                           method=self._client.property)
        meta = _initiate_meta(kwargs, activity=self.activity)

        meta.update({
            AssociatedObjectId.PROPERTY_INSTANCE_ID: attachment_property.id,
            MetaWidget.ALIGNMENT: check_enum(alignment, Alignment, "alignment"),
            MetaWidget.IMAGE_FIT: check_enum(image_fit, ImageFitValue, "image_fit"),
            MetaWidget.SHOW_DOWNLOAD_BUTTON: check_type(show_download_button, bool, "show_download_button"),
            MetaWidget.SHOW_FULL_SCREEN_IMAGE_BUTTON: check_type(show_full_screen_button, bool,
                                                                 "show_full_screen_button"),
        })

        for deprecated_kw in ["widget_type", "readable_models"]:
            if deprecated_kw in kwargs:
                kwargs.pop(deprecated_kw)
                warnings.warn("Argument `{}` is no longer supported as input to `add_attachment_viewer`.".format(
                    deprecated_kw), Warning)

        meta, title = _set_title(meta, title=title, **kwargs)

        if check_type(editable, bool, "editable"):
            kwargs.update({"writable_models": [attachment_property.model_id]})
        else:
            kwargs.update({"readable_models": [attachment_property.model_id]})

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
        from pykechain.models import Activity

        set_of_expected_keys = {AssociatedObjectId.ACTIVITY_ID,
                                MetaWidget.CUSTOM_TEXT,
                                MetaWidget.EMPHASIZED,
                                MetaWidget.EMPHASIZE,
                                MetaWidget.IS_DISABLED,
                                MetaWidget.LINK}
        task_buttons = list()
        for nr, input_dict in enumerate(activities):
            if not set(input_dict.keys()).issubset(set_of_expected_keys):
                raise IllegalArgumentError("Found unexpected key in activities. Only keys allowed are: {}".
                                           format(set_of_expected_keys))
            button_dict = dict()
            task_buttons.append(button_dict)

            if AssociatedObjectId.ACTIVITY_ID in input_dict:
                # Check whether the activityId is class `Activity` or UUID
                activity = input_dict[AssociatedObjectId.ACTIVITY_ID]
                if isinstance(activity, Activity):
                    button_dict[AssociatedObjectId.ACTIVITY_ID] = activity.id
                elif isinstance(activity, str) and is_uuid(activity):
                    button_dict[AssociatedObjectId.ACTIVITY_ID] = activity
                else:
                    raise IllegalArgumentError("When using the add_navigation_bar_widget, activityId must be an "
                                               "Activity or Activity id. Type is: {}".format(type(activity)))
            elif MetaWidget.LINK in input_dict:
                if not is_url(input_dict[MetaWidget.LINK]):
                    raise IllegalArgumentError("The link should be an URL, got '{}'".format(input_dict["link"]))
                button_dict[MetaWidget.LINK] = input_dict[MetaWidget.LINK]
            else:
                raise IllegalArgumentError("Each button must have key 'activityId' or 'link'. "
                                           "Button {} has neither.".format(nr + 1))

            if MetaWidget.CUSTOM_TEXT not in input_dict or not input_dict[MetaWidget.CUSTOM_TEXT]:
                button_dict[MetaWidget.CUSTOM_TEXT] = str()
            else:
                button_dict[MetaWidget.CUSTOM_TEXT] = str(input_dict[MetaWidget.CUSTOM_TEXT])

            button_dict[MetaWidget.EMPHASIZE] = input_dict.get(MetaWidget.EMPHASIZE, False)

            button_dict[MetaWidget.IS_DISABLED] = input_dict.get(MetaWidget.IS_DISABLED, False)

        meta = _initiate_meta(kwargs, activity=self.activity, ignores=(MetaWidget.SHOW_HEIGHT_VALUE,))
        meta[MetaWidget.TASK_BUTTONS] = task_buttons
        meta[MetaWidget.ALIGNMENT] = check_enum(alignment, Alignment, "alignment")

        widget = self.create_widget(
            widget_type=WidgetTypes.TASKNAVIGATIONBAR,
            meta=meta,
            parent=parent_widget,
            **kwargs
        )

        return widget

    def add_propertygrid_widget(self,
                                part_instance: Union['Part', Text],
                                title: TITLE_TYPING = False,
                                max_height: Optional[int] = None,
                                show_headers: Optional[bool] = True,
                                show_columns: Optional[Iterable[ShowColumnTypes]] = None,
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
        part_instance: 'Part' = _retrieve_object(part_instance, method=self._client.part)  # noqa: F821

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

        meta = _initiate_meta(kwargs=kwargs, activity=self.activity)
        meta.update({
            MetaWidget.CUSTOM_HEIGHT: max_height if max_height else None,
            AssociatedObjectId.PART_INSTANCE_ID: part_instance.id,
            MetaWidget.SHOW_COLUMNS: show_columns,
            MetaWidget.SHOW_HEADERS: show_headers,
        })

        meta, title = _set_title(meta, title=title, **kwargs)

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

    def add_service_widget(
            self,
            service: 'Service',
            title: TITLE_TYPING = False,
            custom_button_text: TITLE_TYPING = False,
            emphasize_run: Optional[bool] = True,
            alignment: Optional[Alignment] = Alignment.LEFT,
            download_log: Optional[bool] = False,
            show_log: Optional[bool] = True,
            parent_widget: Optional[Union[Widget, Text]] = None,
            **kwargs
    ) -> Widget:
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
        :param alignment: Horizontal alignment of the button
        :type alignment: Alignment
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
        service: 'Service' = _retrieve_object(obj=service, method=self._client.service)  # noqa

        meta = _initiate_meta(kwargs=kwargs, activity=self.activity)
        meta, title = _set_title(meta, title=title, **kwargs)
        meta = _set_button_text(meta, custom_button_text=custom_button_text, service=service, **kwargs)

        from pykechain.models import Service
        service_id = check_base(service, Service, "service", method=self._client.service)

        meta.update({
            AssociatedObjectId.SERVICE_ID: service_id,
            MetaWidget.EMPHASIZE_BUTTON: emphasize_run,
            MetaWidget.SHOW_DOWNLOAD_LOG: check_type(download_log, bool, "download_log"),
            MetaWidget.SHOW_LOG: True if download_log else check_type(show_log, bool, "show_log"),
            MetaWidget.ALIGNMENT: check_enum(alignment, Alignment, "alignment"),
        })

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
                        title: TITLE_TYPING = None,
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
        check_text(html, "html")

        meta = _initiate_meta(kwargs, activity=self.activity)
        meta, title = _set_title(meta, title=title, **kwargs)

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
                            title: TITLE_TYPING = False,
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

        meta = _initiate_meta(kwargs=kwargs, activity=self.activity)
        meta, title = _set_title(meta, title=title, **kwargs)

        meta.update({
            AssociatedObjectId.SERVICE_ID: notebook_id
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
                             breadcrumb_root: Optional['Activity'] = None,
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
        :param breadcrumb_root: Activity object or UUID to specify the breadcrumb root
        :type breadcrumb_root: Activity
        :param kwargs: additional keyword arguments to pass
        :return: newly created widget
        :rtype: Widget
        :raises IllegalArgumentError: when incorrect arguments are provided
        :raises APIError: When the widget could not be created.
        """
        meta = _initiate_meta(kwargs, activity=self.activity)

        if show_all:
            meta[MetaWidget.SHOW_ALL] = True
        else:
            from pykechain.models import Activity
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
                breadcrumbAncestor=check_base(breadcrumb_root, Activity, "breadcrumb_root") or None,
            ))
        if progress_bar:
            meta.update(dict(
                progressBarSettings=dict(
                    colorNoProgress=progress_bar.get(MetaWidget.COLOR_NO_PROGRESS,
                                                     ProgressBarColors.DEFAULT_NO_PROGRESS),
                    showProgressText=progress_bar.get(MetaWidget.SHOW_PROGRESS_TEXT, True),
                    customHeight=progress_bar.get(MetaWidget.CUSTOM_HEIGHT, 25),
                    colorInProgress=progress_bar.get(MetaWidget.COLOR_IN_PROGRESS,
                                                     ProgressBarColors.DEFAULT_IN_PROGRESS),
                    colorCompleted=progress_bar.get(MetaWidget.COLOR_COMPLETED_PROGRESS,
                                                    ProgressBarColors.DEFAULT_COMPLETED),
                    colorInProgressBackground=progress_bar.get(MetaWidget.COLOR_IN_PROGRESS_BACKGROUND,
                                                               ProgressBarColors.DEFAULT_IN_PROGRESS_BACKGROUND),
                )
            ))
        widget = self.create_widget(
            widget_type=WidgetTypes.METAPANEL,
            title=kwargs.pop(MetaWidget.TITLE, WidgetTypes.METAPANEL),
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
        meta = _initiate_meta(kwargs, activity=self.activity)

        meta.update({
            MetaWidget.COLOR_NO_PROGRESS: color_no_progress,
            MetaWidget.SHOW_PROGRESS_TEXT: show_progress_text,
            MetaWidget.CUSTOM_HEIGHT: height,
            MetaWidget.COLOR_IN_PROGRESS: color_in_progress,
            MetaWidget.COLOR_COMPLETED_PROGRESS: color_completed,
            MetaWidget.COLOR_IN_PROGRESS_BACKGROUND: color_in_progress_background
        })
        widget = self.create_widget(
            widget_type=WidgetTypes.PROGRESS,
            meta=meta,
            **kwargs
        )
        return widget

    def add_multicolumn_widget(self,
                               title: TITLE_TYPING = None,
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
        meta = _initiate_meta(kwargs=kwargs, activity=self.activity)
        meta, title = _set_title(meta, title=title, **kwargs)

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
                         title: TITLE_TYPING = None,
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
        Add a KE-chain Scope widget to the WidgetManager and the activity.

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
        meta = _initiate_meta(kwargs, activity=self.activity)
        meta, title = _set_title(meta, title=title, **kwargs)

        check_type(show_all_columns, bool, "show_all_columns")

        if not show_all_columns and show_columns:
            if not isinstance(show_columns, (list, tuple)):
                raise IllegalArgumentError("`show_columns` must be a list or tuple, `{}` is not.".format(show_columns))
            options = set(ScopeWidgetColumnTypes.values())
            if not all(sc in options for sc in show_columns):
                raise IllegalArgumentError("`show_columns` must consist out of ScopeWidgetColumnTypes options.")
            meta[MetaWidget.SHOW_COLUMNS] = [snakecase(c) for c in show_columns]

        if not isinstance(page_size, int) or page_size < 1:
            raise IllegalArgumentError("`page_size` must be a positive integer, `{}` is not.".format(page_size))

        if team:
            meta[AssociatedObjectId.TEAM_ID] = _retrieve_object_id(team)

        for button_setting in [
            add, edit, delete, clone, emphasize_add, emphasize_clone, emphasize_edit, emphasize_delete,
        ]:
            check_type(button_setting, bool, "buttons")

        meta.update({
            MetaWidget.SORTED_COLUMN: snakecase(check_enum(sorted_column, ScopeWidgetColumnTypes, "sorted_column")),
            MetaWidget.SORTED_DIRECTION: check_enum(sorted_direction, SortTable, "sorted_direction"),
            MetaWidget.VISIBLE_ACTIVE_FILTER: check_type(active_filter, bool, "active_filter"),
            MetaWidget.VISIBLE_SEARCH_FILTER: check_type(search_filter, bool, "search_filter"),
            MetaWidget.VISIBLE_ADD_BUTTON: add,
            MetaWidget.VISIBLE_EDIT_BUTTON: edit,
            MetaWidget.VISIBLE_DELETE_BUTTON: delete,
            MetaWidget.VISIBLE_CLONE_BUTTON: clone,
            MetaWidget.EMPHASIZE_ADD_BUTTON: emphasize_add,
            MetaWidget.EMPHASIZE_EDIT_BUTTON: emphasize_edit,
            MetaWidget.EMPHASIZE_CLONE_BUTTON: emphasize_clone,
            MetaWidget.EMPHASIZE_DELETE_BUTTON: emphasize_delete,
            MetaWidget.CUSTOM_PAGE_SIZE: page_size,
            MetaWidget.TAGS: check_list_of_text(tags, "tags", True) or [],
        })

        widget = self.create_widget(
            widget_type=WidgetTypes.SCOPE,
            title=title,
            meta=meta,
            parent=parent_widget,
            **kwargs
        )
        return widget

    def add_signature_widget(
            self,
            attachment_property: 'AttachmentProperty',
            title: TITLE_TYPING = False,
            parent_widget: Optional[Union[Widget, Text]] = None,
            custom_button_text: Optional[Union[bool, Text]] = False,
            custom_undo_button_text: Optional[Union[bool, Text]] = False,
            editable: Optional[bool] = True,
            **kwargs
    ) -> Widget:
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
        :param parent_widget: (O) parent of the widget for Multicolumn and Multirow widget.
        :type parent_widget: Widget or basestring or None
        :param custom_button_text: Custom text for 'Add signature' button
        :type custom_button_text: bool or basestring
        :param custom_undo_button_text: Custom text for 'Remove signature' button
        :type custom_undo_button_text: bool or basestring
        :param editable: (optional) if False, creates a viewable, not editable, signature widget (default = True)
        :type editable: bool
        :param kwargs: additional keyword arguments to pass
        :return: newly created widget
        :rtype: Widget
        :raises IllegalArgumentError: when incorrect arguments are provided
        :raises APIError: When the widget could not be created.
        """
        attachment_property: 'AttachmentProperty' = _retrieve_object(attachment_property,
                                                                     method=self._client.property)  # noqa
        meta = _initiate_meta(kwargs, activity=self.activity)
        meta, title = _set_title(meta, title=title, **kwargs)
        check_type(editable, bool, "editable")

        # Add custom button text
        if not custom_button_text:
            show_button_value = MetaWidget.BUTTON_TEXT_DEFAULT
            button_text = str()
        else:
            show_button_value = MetaWidget.BUTTON_TEXT_CUSTOM
            button_text = str(custom_button_text)

        # Add custom undo button text
        if not custom_undo_button_text:
            show_undo_button_value = MetaWidget.BUTTON_TEXT_DEFAULT
            undo_button_text = str()
        else:
            show_undo_button_value = MetaWidget.BUTTON_TEXT_CUSTOM
            undo_button_text = str(custom_undo_button_text)

        meta.update({
            AssociatedObjectId.PROPERTY_INSTANCE_ID: attachment_property.id,
            MetaWidget.SHOW_UNDO_BUTTON: show_undo_button_value,
            MetaWidget.CUSTOM_UNDO_BUTTON_TEXT: undo_button_text,
            MetaWidget.CUSTOM_TEXT: button_text,
            MetaWidget.SHOW_BUTTON_VALUE: show_button_value
        })

        widget = self.create_widget(
            widget_type=WidgetTypes.SIGNATURE,
            meta=meta,
            title=title,
            parent=parent_widget,
            readable_models=[attachment_property.model_id] if not editable else None,
            writable_models=[attachment_property.model_id] if editable else None,
            **kwargs,
        )
        return widget

    def add_card_widget(self,
                        image: Optional['AttachmentProperty'] = None,
                        title: TITLE_TYPING = False,
                        parent_widget: Optional[Union[Widget, Text]] = None,
                        description: Optional[Union[Text, bool]] = None,
                        link: Optional[Union[type(None), Text, bool, KEChainPages]] = None,
                        link_value: Optional[CardWidgetLinkValue] = None,
                        link_target: Optional[Union[Text, LinkTargets]] = LinkTargets.SAME_TAB,
                        image_fit: Optional[Union[Text, ImageFitValue]] = ImageFitValue.CONTAIN,
                        **kwargs) -> Widget:
        """
        Add a KE-chain Card widget to the WidgetManager and the activity.

        The widget will be saved in KE-chain.

        :param image: AttachmentProperty providing the source of the image shown in the card widget.
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
            * task: another KE-chain task, provided as an Activity object or its UUID
            * String value: URL to a webpage
            * KE-chain page: built-in KE-chain page of the current scope
        :param parent_widget: (O) parent of the widget for Multicolumn and Multirow widget.
        :type parent_widget: Widget or basestring or None
        :param link_value: Overwrite the default link value (obtained from the type of the link)
        :type link_value: CardWidgetLinkValue
        :param link_target: how the link is opened, one of the values of CardWidgetLinkTarget enum.
        :type link_target: CardWidgetLinkTarget
        :param image_fit: how the image on the card widget is displayed
        :type image_fit: ImageFitValue
        :return: Card Widget
        """
        meta = _initiate_meta(kwargs, activity=self.activity)
        meta, title = _set_title(meta, title=title, **kwargs)
        meta = _set_description(meta, description=description, **kwargs)
        meta = _set_link(meta, link=link, link_value=link_value, link_target=link_target, **kwargs)
        meta = _set_image(meta, image=image, image_fit=image_fit, **kwargs)

        widget = self.create_widget(
            widget_type=WidgetTypes.CARD,
            meta=meta,
            title=title,
            parent=parent_widget,
            **kwargs
        )
        return widget

    def add_weather_widget(self,
                           weather_property: 'Property',
                           autofill: Optional[bool] = None,
                           title: TITLE_TYPING = False,
                           parent_widget: Optional[Union[Widget, Text]] = None,
                           **kwargs) -> Widget:
        """
        Add a KE-chain Weather widget to the Widgetmanager and the activity.

        The widget will be saved in KE-chain.

        :param weather_property: KE-chain Weather property to display
        :type weather_property: Property
        :param title: A custom title for the script widget
            * False (default): Script name
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
        weather_property: 'Property' = _retrieve_object(weather_property, method=self._client.property)  # noqa
        meta = _initiate_meta(kwargs, activity=self.activity)
        meta, title = _set_title(meta, title=title, **kwargs)

        meta.update({
            AssociatedObjectId.PROPERTY_INSTANCE_ID: weather_property.id,
        })

        widget = self.create_widget(
            widget_type=WidgetTypes.WEATHER,
            meta=meta,
            title=title,
            parent=parent_widget,
            writable_models=[weather_property.model_id],
            **kwargs,
        )
        return widget

    def add_service_card_widget(
            self,
            service: 'Service',
            image: Optional['AttachmentProperty'] = None,
            title: TITLE_TYPING = False,
            description: Optional[Union[Text]] = None,
            parent_widget: Optional[Union[Widget, Text]] = None,
            custom_button_text: TITLE_TYPING = False,
            emphasize_run: Optional[bool] = True,
            alignment: Optional[Alignment] = Alignment.LEFT,
            link: Optional[Union[type(None), Text, bool, KEChainPages]] = None,
            link_value: Optional[CardWidgetLinkValue] = None,
            link_target: Optional[Union[Text, LinkTargets]] = LinkTargets.SAME_TAB,
            image_fit: Optional[Union[ImageFitValue, Text]] = ImageFitValue.CONTAIN,
            **kwargs
    ) -> Widget:
        """
        Add a KE-chain Service Card widget to the WidgetManager and the activity.

        The widget will be saved in KE-chain.

        :param service: The Service to which the button will be coupled and will be ran when the button is pressed.
        :type service: :class:`Service` or UUID
        :param image: AttachmentProperty providing the source of the image shown in the card widget.
        :param title: A custom title for the card widget
            * False (default): Card name
            * String value: Custom title
            * None: No title
        :param description: Custom text shown below the image in the card widget
            * False (default): Card name
            * String value: Custom title
            * None: No title
        :param parent_widget: (O) parent of the widget for Multicolumn and Multirow widget.
        :type parent_widget: Widget or basestring or None
        :param custom_button_text: A custom text for the button linked to the script
            * False (default): Script name
            * String value: Custom title
            * None: No title
        :type custom_button_text: bool or basestring or None
        :param emphasize_run: Emphasize the run button (default True)
        :type emphasize_run: bool
        :param alignment: Horizontal alignment of the button
        :type alignment: Alignment
        :param link: Where the card widget refers to. This can be one of the following:
            * None (default): no link
            * task: another KE-chain task, provided as an Activity object or its UUID
            * String value: URL to a webpage
            * KE-chain page: built-in KE-chain page of the current scope
        :param link_value: Overwrite the default link value (obtained from the type of the link)
        :type link_value: CardWidgetLinkValue
        :param link_target: how the link is opened, one of the values of CardWidgetLinkTarget enum.
        :type link_target: CardWidgetLinkTarget
        :param image_fit: how the image on the card widget is displayed
        :type image_fit: ImageFitValue
        :return: Service Card Widget
        """
        # Check whether the script is uuid type or class `Service`
        service: 'Service' = _retrieve_object(obj=service, method=self._client.service)  # noqa

        meta = _initiate_meta(kwargs=kwargs, activity=self.activity)
        meta, title = _set_title(meta, title=title, **kwargs)
        meta = _set_description(meta, description=description, **kwargs)
        meta = _set_link(meta, link=link, link_value=link_value, link_target=link_target, **kwargs)
        meta = _set_image(meta, image=image, image_fit=image_fit, **kwargs)
        meta = _set_button_text(meta, custom_button_text=custom_button_text, service=service, **kwargs)

        from pykechain.models import Service
        service_id = check_base(service, Service, "service", method=self._client.service)

        meta.update({
            AssociatedObjectId.SERVICE_ID: service_id,
            MetaWidget.EMPHASIZE_BUTTON: emphasize_run,
            MetaWidget.ALIGNMENT: check_enum(alignment, Alignment, "alignment"),
        })

        widget = self.create_widget(
            widget_type=WidgetTypes.SERVICECARD,
            meta=meta,
            title=title,
            parent=parent_widget,
            **kwargs
        )
        return widget

    def add_dashboard_widget(
            self,
            title: TITLE_TYPING = False,
            parent_widget: Optional[Union[Widget, Text]] = None,
            source_scopes: Optional[DashboardWidgetSourceScopes] = DashboardWidgetSourceScopes.CURRENT_SCOPE,
            source_scopes_tags: Optional[List] = None,
            source_subprocess: Optional[List] = None,
            source_selected_scopes: Optional[List] = None,
            show_tasks: Optional[List[DashboardWidgetShowTasks]] = None,
            show_scopes: Optional[List[DashboardWidgetShowScopes]] = None,
            no_background: Optional[bool] = False,
            show_assignees: Optional[bool] = True,
            show_assignees_table: Optional[bool] = True,
            show_open_task_assignees: Optional[bool] = True,
            show_open_vs_closed_tasks: Optional[bool] = True,
            show_open_closed_tasks_assignees: Optional[bool] = True,
            **kwargs
    ) -> Widget:
        """
        Add a KE-chain Dashboard Widget to the WidgetManager and the activity.

        The widget will be saved in KE-chain

        :param title: A custom title for the card widget
            * False (default): Card name
            * String value: Custom title
            * None: No title
        :param parent_widget: (O) parent of the widget for Multicolumn and Multirow widget.
        :type parent_widget: Widget or basestring or None
        :param source_scopes: The `Project(s)` to be used as source when displaying the Widget.
            Defaults on CURRENT_SCOPE.
        :type source_scopes: basestring (see :class:`models.widgets.enums.DashboardWidgetSourceScopes`)
        :param source_scopes_tags: Tags on which the source projects can be filtered on. Source is selected
            automatically as TAGGED_SCOPES
        :type source_scopes_tags: list of tags
        :param source_subprocess: Subprocess that the `Widget` uses as source. Source is selected automatically
            SUBPROCESS
        :type source_subprocess: list of str (UUID of an `Activity`)
        :param source_selected_scopes: List of `Scope` to be used by the `Widget` as source. Source is selected
            automatically as SELECTED_SCOPES
        :type source_selected_scopes: list of str (UUIDs of `Scopes`)
        :param show_tasks: Type of tasks to be displayed in the `Widget`. If left None, all of them will be selected
        :type show_tasks: list of basestring (see :class:`models.widgets.enums.DashboardWidgetShowTasks`)
        :param show_scopes: Type of scopes to be displayed in the `Widget`. If left None, all of them will be selected
        :type show_scopes: list of basestring (see :class:`models.widgets.enums.DashboardWidgetShowScopes`)
        :param no_background: Reverse the shadows (default False)
        :type no_background: bool
        :param show_assignees: Show the assignees pie chart
        :type show_assignees: bool
        :param show_assignees_table: Show the assignees table
        :type show_assignees_table: bool
        :param show_open_task_assignees: Show the `Open tasks per assignees` pie chart
        :type show_open_task_assignees: bool
        :param show_open_vs_closed_tasks: Show the `Open vs closed tasks` pie chart
        :type show_open_vs_closed_tasks: bool
        :param show_open_closed_tasks_assignees: Show the `Open open and closed tasks per assignees` pie chart
        :type show_open_closed_tasks_assignees: bool
        :param kwargs:
        :return:
        """
        meta = _initiate_meta(kwargs=kwargs, activity=self.activity)
        meta, title = _set_title(meta, title=title, **kwargs)

        if source_scopes_tags:
            meta.update({
                MetaWidget.SOURCE: DashboardWidgetSourceScopes.TAGGED_SCOPES,
                MetaWidget.SCOPE_TAG: check_type(source_scopes_tags, list, "source_scopes_tags")
            })
        elif source_subprocess:
            meta.update({
                MetaWidget.SOURCE: DashboardWidgetSourceScopes.SUBPROCESS,
                MetaWidget.SCOPE_TAG: check_type(source_subprocess, list, "source_subprocess")
            })
        elif source_selected_scopes:
            meta.update({
                MetaWidget.SOURCE: DashboardWidgetSourceScopes.SELECTED_SCOPES,
                MetaWidget.SCOPE_LIST: check_type(source_selected_scopes, list, "source_selected_scopes")
            })
        else:
            meta.update({
                MetaWidget.SOURCE: check_enum(source_scopes, DashboardWidgetSourceScopes, "source_scopes")
            })

        show_tasks_list = list()
        if show_tasks is None:
            for value in DashboardWidgetShowTasks.values():
                show_tasks_list.append({
                    MetaWidget.NAME: value,
                    MetaWidget.ORDER: DashboardWidgetShowTasks.values().index(value),
                    MetaWidget.SELECTED: True
                })
        else:
            check_type(show_tasks, list, "show_tasks")
            for value in DashboardWidgetShowTasks.values():
                if value in show_tasks:
                    show_tasks_list.append({
                        MetaWidget.NAME: value,
                        MetaWidget.ORDER: DashboardWidgetShowTasks.values().index(value),
                        MetaWidget.SELECTED: True
                    })
                else:
                    show_tasks_list.append({
                        MetaWidget.NAME: value,
                        MetaWidget.ORDER: DashboardWidgetShowTasks.values().index(value),
                        MetaWidget.SELECTED: False
                    })

        show_projects_list = list()
        if show_scopes is None:
            for value in DashboardWidgetShowScopes.values():
                show_projects_list.append({
                    MetaWidget.NAME: value,
                    MetaWidget.ORDER: DashboardWidgetShowScopes.values().index(value),
                    MetaWidget.SELECTED: True
                })
        else:
            check_type(show_tasks, list, "show_tasks")
            for value in DashboardWidgetShowScopes.values():
                if value in show_scopes:
                    show_projects_list.append({
                        MetaWidget.NAME: value,
                        MetaWidget.ORDER: DashboardWidgetShowScopes.values().index(value),
                        MetaWidget.SELECTED: True
                    })
                else:
                    show_projects_list.append({
                        MetaWidget.NAME: value,
                        MetaWidget.ORDER: DashboardWidgetShowScopes.values().index(value),
                        MetaWidget.SELECTED: False
                    })
        meta.update({
            MetaWidget.SHOW_NUMBERS: show_tasks_list,
            MetaWidget.SHOW_NUMBERS_PROJECTS: show_projects_list,
            MetaWidget.NO_BACKGROUND: check_type(no_background, bool, "no_background"),
            MetaWidget.SHOW_ASSIGNEES: check_type(show_assignees, bool, "show_assignees"),
            MetaWidget.SHOW_ASSIGNEES_TABLE: check_type(show_assignees_table, bool, "show_assignees_table"),
            MetaWidget.SHOW_OPEN_TASK_ASSIGNEES: check_type(show_open_task_assignees, bool, "show_open_task_assignees"),
            MetaWidget.SHOW_OPEN_VS_CLOSED_TASKS: check_type(show_open_vs_closed_tasks, bool,
                                                             "show_open_vs_closed_tasks"),
            MetaWidget.SHOW_OPEN_VS_CLOSED_TASKS_ASSIGNEES: check_type(
                show_open_closed_tasks_assignees, bool, "show_open_closed_tasks_assignees")
        })

        widget = self.create_widget(
            widget_type=WidgetTypes.DASHBOARD,
            meta=meta,
            title=title,
            parent=parent_widget,
            **kwargs
        )
        return widget

    def add_tasks_widget(
            self,
            title: TITLE_TYPING = False,
            parent_widget: Optional[Union[Widget, Text]] = None,
            add: Optional[bool] = True,
            clone: Optional[bool] = True,
            edit: Optional[bool] = True,
            delete: Optional[bool] = True,
            emphasize_add: Optional[bool] = True,
            emphasize_clone: Optional[bool] = False,
            emphasize_edit: Optional[bool] = False,
            emphasize_delete: Optional[bool] = False,
            show_my_tasks_filter: Optional[bool] = True,
            show_open_tasks_filter: Optional[bool] = True,
            show_search_filter: Optional[bool] = True,
            parent_activity: Optional[Union['Activity', Text]] = None,
            assigned_filter: Optional[TasksAssignmentFilterTypes] = TasksAssignmentFilterTypes.ALL,
            status_filter: Optional[ActivityStatus] = None,
            activity_type_filter: Optional[ActivityType] = ActivityType.TASK,
            classification_filter: Optional[ActivityClassification] = ActivityClassification.WORKFLOW,
            tags_filter: Optional[List[Text]] = (),
            collapse_filter: Optional[bool] = False,
            show_columns: Optional[List[TasksWidgetColumns]] = None,
            sorted_column: Optional[TasksWidgetColumns] = None,
            sorted_direction: Optional[SortTable] = SortTable.ASCENDING,
            page_size: Optional[int] = 25,
            **kwargs
    ) -> Widget:
        """
        Add a KE-chain Tasks Widget to the WidgetManager and the activity.

        The widget will be saved in KE-chain

        :param title: A custom title for the card widget
            * False (default): Card name
            * String value: Custom title
            * None: No title
        :param parent_widget: (O) parent of the widget for Multicolumn and Multirow widget.
        :type parent_widget: Widget or basestring or None
        :param add: Show the "add task" button, only visible if a `parent_activity` is provided (default = True)
        :type add: bool
        :param clone: Show the "clone task" button (default = True)
        :type clone: bool
        :param edit: Show the "edit task" button (default = True)
        :type edit: bool
        :param delete: Show the "delete task" button (default = True)
        :type delete: bool
        :param emphasize_add: Show green backdrop for "add task" button (default = True)
        :type emphasize_add: bool
        :param emphasize_clone: Show green backdrop for "clone task" button (default = False)
        :type emphasize_clone: bool
        :param emphasize_edit: Show green backdrop for "edit task" button (default = False)
        :type emphasize_edit: bool
        :param emphasize_delete: Show green backdrop for "delete task" button (default = False)
        :type emphasize_delete: bool
        :param show_my_tasks_filter: Show the switch to filter on assigned tasks (default = True)
        :type show_my_tasks_filter: bool
        :param show_open_tasks_filter: Show the switch to filter on tasks with status OPEN (default = True)
        :type show_open_tasks_filter: bool
        :param show_search_filter: Show textfield to filter on a task name (default = True)
        :type show_search_filter: bool
        :param parent_activity: Filter on task parent Activity, thereby enabling the "add task" button
        :type parent_activity: Activity
        :param assigned_filter: Filter on the assignment of the tasks (default = ALL)
        :type assigned_filter: TasksAssignmentFilterTypes
        :param status_filter: Filter on the status of the tasks (default = OPEN)
        :type status_filter: ActivityStatus
        :param activity_type_filter: Filter on the activity type (default = TASK)
        :type activity_type_filter: ActivityType
        :param classification_filter: Filter on the activity classification (default = WORKFLOW)
        :type classification_filter: ActivityClassification
        :param tags_filter: Filter on list of tags
        :type tags_filter: list
        :param collapse_filter: Collapse the filter pane, or hide the pane if `None` (default = False)
        :type collapse_filter: bool
        :param show_columns: List of task attributes to show (default = all)
        :type show_columns: list
        :param sorted_column: Task attribute to sort on (default = no sorting)
        :type sorted_column: TasksWidgetColumns
        :param sorted_direction: Direction of sorting (default = ascending)
        :type sorted_direction: SortTable
        :param page_size: Number of tasks to show per pagination (default = 25)
        :type page_size: int
        :return: Task widget
        :rtype Widget
        """
        meta = _initiate_meta(kwargs=kwargs, activity=self.activity)
        meta, title = _set_title(meta, title=title, **kwargs)

        from pykechain.models import Activity
        filters = {
            MetaWidget.PARENT_ACTIVITY_ID: check_base(parent_activity, Activity, "parent_activity"),
            MetaWidget.ASSIGNED:
                check_enum(assigned_filter, TasksAssignmentFilterTypes, "assigned_filter"),
            MetaWidget.ACTIVITY_STATUS:
                check_enum(status_filter, ActivityStatus, "status_filter") or "",
            MetaWidget.ACTIVITY_TYPE:
                check_enum(activity_type_filter, ActivityType, "activity_type_filter"),
            MetaWidget.ACTIVITY_CLASSIFICATION:
                check_enum(classification_filter, ActivityClassification, "classification_filter"),
            MetaWidget.TAGS_FILTER:
                check_list_of_text(tags_filter, "tags_filter", unique=True),
        }

        meta.update({
            MetaWidget.VISIBLE_ADD_BUTTON: check_type(add, bool, "add") if parent_activity else None,
            MetaWidget.VISIBLE_CLONE_BUTTON: check_type(clone, bool, "clone"),
            MetaWidget.VISIBLE_EDIT_BUTTON: check_type(edit, bool, "edit"),
            MetaWidget.VISIBLE_DELETE_BUTTON: check_type(delete, bool, "delete"),
            MetaWidget.EMPHASIZE_ADD_BUTTON: check_type(emphasize_add, bool, "emphasize_add"),
            MetaWidget.EMPHASIZE_CLONE_BUTTON: check_type(emphasize_clone, bool, "emphasize_clone"),
            MetaWidget.EMPHASIZE_EDIT_BUTTON: check_type(emphasize_edit, bool, "emphasize_edit"),
            MetaWidget.EMPHASIZE_DELETE_BUTTON: check_type(emphasize_delete, bool, "emphasize_delete"),
            MetaWidget.VISIBLE_MY_TASKS_FILTER: check_type(show_my_tasks_filter, bool, "show_my_tasks_filter"),
            MetaWidget.VISIBLE_OPEN_TASKS_FILTER: check_type(show_open_tasks_filter, bool, "show_open_tasks_filter"),
            MetaWidget.VISIBLE_SEARCH_FILTER: check_type(show_search_filter, bool, "show_search_filter"),
            MetaWidget.PREFILTERS: filters,
            MetaWidget.COLLAPSE_FILTERS: check_type(collapse_filter, bool, "collapse_filter"),
            MetaWidget.SHOW_FILTERS: collapse_filter is not None,
            MetaWidget.SHOW_COLUMNS: check_list_of_text(show_columns, "show_columns") or TasksWidgetColumns.values(),
            MetaWidget.SORTED_COLUMN: check_enum(sorted_column, TasksWidgetColumns, "sorted_column"),
            MetaWidget.SORTED_DIRECTION: check_enum(sorted_direction, SortTable, "sorted_direction"),
            MetaWidget.CUSTOM_PAGE_SIZE: check_type(page_size, int, "page_size"),
        })

        widget = self.create_widget(
            widget_type=WidgetTypes.TASKS,
            meta=meta,
            title=title,
            parent=parent_widget,
            **kwargs
        )

        return widget

    def add_scopemembers_widget(
            self,
            title: TITLE_TYPING = False,
            parent_widget: Optional[Union[Widget, Text]] = None,
            add: Optional[bool] = True,
            edit: Optional[bool] = True,
            remove: Optional[bool] = True,
            show_username_column: Optional[bool] = True,
            show_name_column: Optional[bool] = True,
            show_email_column: Optional[bool] = True,
            show_role_column: Optional[bool] = True,
            **kwargs
    ) -> Widget:
        """
        Add a KE-chain Scope Members Widget to the WidgetManager and the activity.

        The widget will be saved in KE-chain

        :param title: A custom title for the card widget
            * False (default): Card name
            * String value: Custom title
            * None: No title
        :param parent_widget: (O) parent of the widget for Multicolumn and Multirow widget.
        :type parent_widget: Widget or basestring or None
        :param add: Show "add user" button (default = True)
        :type add: bool
        :param edit: Show "edit role" button (default = True)
        :type edit: bool
        :param remove: Show "remove user" button (default = True)
        :type remove: bool
        :param show_username_column: Show "username" column (default = True)
        :type show_username_column: bool
        :param show_name_column: Show "name" column (default = True)
        :type show_name_column: bool
        :param show_email_column: Show "email" column (default = True)
        :type show_email_column: bool
        :param show_role_column: Show "role" column (default = True)
        :type show_role_column: bool
        :return: Scope members Widget
        :rtype Widget
        """
        meta = _initiate_meta(kwargs=kwargs, activity=self.activity)
        meta, title = _set_title(meta, title=title, **kwargs)

        meta.update({
            MetaWidget.SHOW_ADD_USER_BUTTON: check_type(add, bool, "add"),
            MetaWidget.SHOW_EDIT_ROLE_BUTTON: check_type(edit, bool, "edit"),
            MetaWidget.SHOW_REMOVE_USER_BUTTON: check_type(remove, bool, "remove"),
            MetaWidget.SHOW_USERNAME_COLUMN: check_type(show_username_column, bool, "show_username_columns"),
            MetaWidget.SHOW_NAME_COLUMN: check_type(show_name_column, bool, "show_name_column"),
            MetaWidget.SHOW_EMAIL_COLUMN: check_type(show_email_column, bool, "show_email_column"),
            MetaWidget.SHOW_ROLE_COLUMN: check_type(show_role_column, bool, "show_role_column"),
        })

        widget = self.create_widget(
            widget_type=WidgetTypes.SCOPEMEMBERS,
            meta=meta,
            title=title,
            parent=parent_widget,
            **kwargs
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
