from abc import abstractmethod, ABC
from typing import Optional, Any, Text, Iterable, Union, Tuple, List

from pykechain.models import Property2, Base
from pykechain.models.base import BaseInScope
from pykechain.utils import is_uuid


class _ReferenceProperty(Property2):
    """
    Private base class for the KE-chain reference properties.

    .. versionadded:: 3.7
    :cvar REFERENCED_CLASS: handle to the Pykechain class that is referenced using this ReferenceProperty class.
    """

    REFERENCED_CLASS = Base  # type: type(Base)

    def __init__(self, json, **kwargs):
        """Construct a ReferenceProperty from a json object."""
        super().__init__(json, **kwargs)

        self._cached_values = None

    @property
    def ref_name(self) -> Text:
        """Get the name of the referenced Pykechain class."""
        return self.REFERENCED_CLASS.__name__

    @property
    def value(self) -> Optional[Iterable[REFERENCED_CLASS]]:
        """
        Retrieve the referenced objects of this reference property.

        :return: list or generator of `Base` objects.
        :rtype list
        """
        if not self._value:
            return None
        elif not self._cached_values:
            self._cached_values = self._retrieve_objects()
        return self._cached_values

    @value.setter
    def value(self, value: Any) -> None:
        if self.use_bulk_update:
            self._pend_value(value)
        else:
            self._put_value(value)

    @abstractmethod
    def _retrieve_objects(self, **kwargs) -> Iterable[Base]:
        """
        Retrieve a list of Pykechain objects, type depending on the reference property type.

        This method is abstract because the exact method of the Client class changes per subclass.

        :param kwargs: optional arguments
        :return: list of Pykechain objects inheriting from Base
        """
        pass

    def serialize_value(self, value: Union[List, Tuple]) -> Optional[List[Text]]:
        """
        Serialize the value to be set on the property by checking for a list of Base objects.

        :param value: non-serialized value
        :type value: Any
        :return: serialized value
        """
        value_to_set = []
        if isinstance(value, (list, tuple)):
            for item in value:
                if isinstance(item, self.REFERENCED_CLASS):
                    value_to_set.append(item.id)
                elif isinstance(item, str) and is_uuid(item):
                    value_to_set.append(item)
                else:
                    raise ValueError("References must be of type {cls}, {cls} id or None. type: {}".format(
                        type(item), cls=self.ref_name))
        elif value is None:
            value_to_set = None  # clear out the list
        else:
            raise ValueError(
                "Reference must be a list (or tuple) of type {cls}, {cls} id or None. type: {}".format(
                    type(value), cls=self.ref_name))

        return value_to_set


class _ReferencePropertyInScope(_ReferenceProperty, ABC):
    """
    Private base class for the KE-chain reference properties pointing to objects confined to a scope.

    .. versionadded:: 3.7
    """

    REFERENCED_CLASS = BaseInScope

    def _put_value(self, value: Union[List, Tuple]):
        super()._put_value(value=value)

        if value is not None:
            self._check_x_scope_id(referenced_object=value)

    def _check_x_scope_id(self, referenced_object: Union[Any, BaseInScope]) -> None:
        """
        Check whether this reference property has the `scope_id` in its `value_options`.

        :param referenced_object: Either a pykechain object or a UUID string.
        :return: None
        """
        if self._options and 'scope_id' not in self._options:
            # See whether the referenced model is an object with an ID
            if isinstance(referenced_object, self.REFERENCED_CLASS):
                x_scope_id = referenced_object.scope_id
            else:
                # retrieve the scope_id from the property model's value (which is an object in a scope (x_scope))
                referenced_models = self.model().value
                if not referenced_models or not isinstance(referenced_models[0], self.REFERENCED_CLASS):
                    # if the referenced model is not set or the referenced value is not in current scope
                    x_scope_id = self.scope_id
                else:
                    # get the scope_id from the referenced model
                    x_scope_id = referenced_models[0].scope_id
            self._options['scope_id'] = x_scope_id

            # edit the model of the property, such that all instances are updated as well.
            self.model().edit(options=self._options)
