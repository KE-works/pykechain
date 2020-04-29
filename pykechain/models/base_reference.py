from abc import abstractmethod
from typing import Optional, Sized, Any, Text, Iterable

from pykechain.models import Property2, Base
from pykechain.utils import is_uuid


class _ReferenceProperty(Property2):

    REFERENCED_CLASS = Base  # type: type(Base)

    def __init__(self, json, **kwargs):
        """Construct a ReferenceProperty from a json object."""
        super().__init__(json, **kwargs)

        self._cached_values = None

    @property
    def cls(self) -> Text:
        return self.REFERENCED_CLASS.__name__

    @property
    def value(self) -> Optional[Sized[Base]]:
        """
        Retrieve the referenced objects of this reference property.

        :return: list or generator of `Base` objects.
        :rtype Sized
        """
        if not self._value:
            return None
        elif not self._cached_values:
            self._cached_values = self._retrieve_objects(object_ids=self._value)
        return self._cached_values

    @abstractmethod
    def _retrieve_objects(self, object_ids: Iterable[Any], **kwargs) -> Sized[Base]:
        pass

    @value.setter
    def value(self, value):
        value_to_set = []
        if isinstance(value, (list, tuple)):
            for item in value:
                if isinstance(item, self.REFERENCED_CLASS):
                    value_to_set.append(item.id)
                elif isinstance(item, str) and is_uuid(item):
                    value_to_set.append(item)
                else:
                    raise ValueError("References must be of {cls}, {cls} id or None. type: {}".format(type(item),
                                                                                                      cls=self.cls))
        elif value is None:
            # clear out the list
            value_to_set = None
        else:
            raise ValueError(
                "Reference must be a list (or tuple) of {cls}, {cls} id or None. type: {}".format(type(value),
                                                                                                  cls=self.cls))

        # consistency check for references model that should include a scope_id in the value_options.
        if self._options and 'scope_id' not in self._options and value_to_set is not None:
            # if value_to_set is not None, retrieve the scope_id from the first value_to_set
            # we do this smart by checking if we got provided a full Part; that is easier.
            if isinstance(value[0], self.REFERENCED_CLASS):
                x_scope_id = value[0].scope_id
            else:
                # retrieve the scope_id from the model value[0] (which is an object in a scope (x_scope))
                referenced_model = self.model().value
                if not referenced_model or not isinstance(referenced_model[0], self.REFERENCED_CLASS):
                    # if the referenced model is not set or the referenced value is not a Part set to current scope
                    x_scope_id = self.scope_id
                else:
                    # get the scope_id from the referenced model
                    x_scope_id = referenced_model[0].scope_id
            self._options['scope_id'] = x_scope_id

            # edit the model of the property, such that all instances are updated as well.
            self.model().edit(options=self._options)

        # do the update
        self._put_value(value_to_set)
