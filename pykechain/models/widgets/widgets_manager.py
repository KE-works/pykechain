import bisect
from typing import Sized

import requests
from six import string_types, text_type

from pykechain.client import API_EXTRA_PARAMS
from pykechain.enums import WidgetTypes
from pykechain.exceptions import NotFoundError, IllegalArgumentError, APIError
from pykechain.models import Property2, Property
from pykechain.models.widgets import Widget
from pykechain.utils import is_uuid, find


class WidgetsManager(Sized):
    def __init__(self, widgets, activity_id=None, client=None, **kwargs):
        self._widgets = list(widgets)
        self._activity_id = activity_id
        self._client = client
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
        found = None
        if isinstance(key, int):
            return self._widgets[key]
        elif is_uuid(key):
            return find(self._widgets, lambda p: key == p.id)
        elif isinstance(key, (string_types, text_type)):
            return find(self._widgets, lambda p: key == p.name)

        raise NotFoundError("Could not find widget with index, name or id {}".format(key))

    def create_widget(self, widget_type=WidgetTypes.UNDEFINED,
                      title=None, meta=None, order=None, parent_id=None,
                      inputs=None, outputs=None):
        if widget_type is not None and not isinstance(widget_type, text_type) \
                or widget_type not in WidgetTypes.values():
            raise IllegalArgumentError("`widget_type` should be one of '{}'".format(WidgetTypes.values()))

        if title is not None:
            if not isinstance(title, (string_types, text_type)):
                raise IllegalArgumentError("`title` should be provided as a string")

        if order is not None:
            if not isinstance(order, int):
                raise IllegalArgumentError("`order` should be provided as a integer, and unique in the list "
                                           "of widgets")

        if parent_id is not None:
            if isinstance(parent_id, Widget):
                parent_id = parent_id.id
            elif is_uuid(parent_id):
                pass
            else:
                raise IllegalArgumentError("`parent_id` should be provided as a widget or uuid")

        if meta is not None:
            if not isinstance(meta, dict):
                raise IllegalArgumentError("`meta` should be provided as a dictionary with keys according "
                                           "to the schema of the widget_type")

        if inputs is not None:
            if not isinstance(inputs, (list, tuple, set)):
                raise IllegalArgumentError("`inputs` should be provided as a list of uuids or property models")
            readable_model_ids = []
            for input in inputs:
                if is_uuid(input):
                    readable_model_ids.append(input)
                elif isinstance(input, (Property2, Property)):
                    readable_model_ids.append(input.id)
                else:
                    IllegalArgumentError("`inputs` should be provided as a list of uuids or property models")

        if outputs is not None:
            if not isinstance(outputs, (list, tuple, set)):
                raise IllegalArgumentError("`outputs` should be provided as a list of uuids or "
                                           "property models")
            writable_model_ids = []
            for output in outputs:
                if is_uuid(output):
                    writable_model_ids.append(output)
                elif isinstance(output, (Property2, Property)):
                    writable_model_ids.append(output.id)
                else:
                    IllegalArgumentError("`outputs` should be provided as a list of uuids or property models")

        data = dict(
            widget_type=widget_type,
            title=title,
            activity_id=self._activity_id,
            meta=meta,
            widget_options=dict(),
            order=order,
            parent_id=parent_id
        )

        request_params = API_EXTRA_PARAMS['widget']

        response = self._client._request('POST', self._client._build_url('widget'),
                                         params=request_params, data=data)

        if response.status_code != requests.codes.created:
            raise APIError("Could not create widget: {}: {}".format(str(response), response.content))

        widget = Widget.create(json=response.json().get('results')[0], client=self._client)
        if order is None:
            self._widgets.append(widget)
        else:
            self.insert(order, widget)
        return widget

    def insert(self, index, widget):
        # type: (int, Widget) -> None
        """
        Insert a widget at index n, shifting the rest of the list to the right.

        if widget order is [Widget0,Widget1,Widget2] and inserting Widget4 at index 2 (before Widget1);
        the list will be [Widget0, Widget4, Widget1, Widget2]

        :param index: integer (position) starting from 1 at first position in which the widget is inserted
        :type index: int
        :param widget: Widget object to insert
        :type widget: Widget
        :return: None
        :raises IndexError: The index is out of range
        :raises APIError: The list of widgets could not be updated
        """
        if index < self.__len__():
            raise IndexError("The index is out of range. "
                             "The list of widgets is '{}' widget(s) long.".format(self.__len__()))

        bisect.insort(self._widgets, widget)

        # bulk update the order of the widgets:
        fvalues = [dict(id=w.id, order=index) for index, w in enumerate(self._widgets)]

        response = self._client._request("PUT", self._client._build_url('widgets'),
                                         params=API_EXTRA_PARAMS['widgets'],
                                         data=fvalues)

        if response.status_code != requests.codes.ok:
            raise APIError("Could not update the order of the widgets: {}: {}".format(str(response),
                                                                                      response.content))

        widgets_response = response.json().get('results')
        for widget, updated_response in self._widgets, widgets_response:
            widget.refresh(json=updated_response)
