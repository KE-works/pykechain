from six import string_types, text_type
from typing import Sized

from pykechain.exceptions import NotFoundError
from pykechain.utils import is_uuid, find


class WidgetSet(Sized):
    def __init__(self, widgets):
        self._widgets = list(widgets)
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
        elif isinstance(key,  (string_types, text_type)):
            return find(self._widgets, lambda p: key == p.name)

        raise NotFoundError("Could not find widget with index, name or id {}".format(key))
