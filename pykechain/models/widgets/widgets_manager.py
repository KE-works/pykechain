import bisect
from typing import Sized, Any, Iterable, Union, AnyStr, Optional

import requests
from six import string_types, text_type

from pykechain.enums import SortTable, WidgetTypes
from pykechain.exceptions import NotFoundError, APIError, IllegalArgumentError
from pykechain.models.widgets import Widget
from pykechain.models.widgets.helpers import _retrieve_part_model, _retrieve_parent_instance, \
    _retrieve_sort_property_id, _set_title, _initiate_meta
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

    def add_super_grid_widget(self, part_model, parent_instance=None, custom_title=False,
                              delete=False, edit=True, export=True, clone=True, incomplete_rows=True, add=False,
                              emphasize_edit=False, emphasize_add=True,
                              emphasize_clone=False, emphasize_delete=False, sort_property=None,
                              sort_direction=SortTable.ASCENDING, readable_models=None, writable_models=None, **kwargs):
        """

        :param part_model:
        :param parent_instance:
        :param delete:
        :param edit:
        :param export:
        :param clone:
        :param incomplete_rows:
        :param add:
        :param emphasize_edit:
        :param emphasize_add:
        :param emphasize_clone:
        :param emphasize_delete:
        :param sort_property_id:
        :param sort_direction:
        :param kwargs:
        :return:
        """
        # Check whether the part_model is uuid type or class `Part`
        part_model = _retrieve_part_model(part_model, client=self._client)  # type: Part2
        parent_instance = _retrieve_parent_instance(parent_instance=parent_instance, client=self._client)  # type: Part2
        sort_property_id = _retrieve_sort_property_id(sort_property=sort_property)  # type: text_type

        meta = _initiate_meta(kwargs=kwargs, activity_id=self._activity_id)
        meta.update({
            # grid
            "partModelId": part_model.id,
            # columns
            # "columns": ,
            "sortedColumn": sort_property_id if sort_property_id else None,
            "sortDirection": sort_direction,
            # buttons
            "addButtonVisible": add,
            "editButtonVisible": edit,
            "deleteButtonVisible": delete,
            "cloneButtonVisible": clone,
            "downloadButtonVisible": export,
            "incompleteRowsVisible": incomplete_rows,
            # "incompleteRowsButtonVisible": def_bool,
            "primaryAddUiValue": emphasize_add,
            "primaryEditUiValue": emphasize_edit,
            "primaryCloneUiValue": emphasize_clone,
            "primaryDeleteUiValue": emphasize_delete,
        })

        if parent_instance:
            meta['parentInstanceId'] = parent_instance.id

        meta, title = _set_title(meta, custom_title, default_title=part_model.name)

        widget = self.create_widget(
            widget_type=WidgetTypes.SUPERGRID,
            title=title,
            meta=meta,
            order=kwargs.get("order"),
            readable_models=readable_models,
            writable_models=writable_models
        )
        print()
        return widget

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
            raise APIError("Could not update the order of the widgets: {}: {}".format(str(response),
                                                                                      response.content))

        widgets_response = response.json().get('results')
        for widget, updated_response in self._widgets, widgets_response:
            widget.refresh(json=updated_response)
