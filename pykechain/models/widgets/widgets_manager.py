import bisect
from typing import Sized, Any

import requests
from six import string_types, text_type

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
        """Widget from the list of widgets based on index, uuid, title or ref"""
        found = None
        if isinstance(key, int):
            found = self._widgets[key]
        elif is_uuid(key):
            found = find(self._widgets, lambda p: key == p.id)
        elif isinstance(key, (string_types, text_type)):
            found =  find(self._widgets, lambda p: key == p.title or key==p.ref)

        if found is not None:
            return found

        raise NotFoundError("Could not find widget with index, title, ref, or id {}".format(key))

    def create_widget(self, *args, **kwargs):

        widget = self._client.create_widget(*args, activity=self._activity_id, **kwargs)

        if kwargs.get('order') is None:
            self._widgets.append(widget)
        else:
            self.insert(kwargs.get('order'), widget)
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
