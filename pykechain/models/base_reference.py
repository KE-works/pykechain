from abc import abstractmethod, ABC
from typing import Optional, Any, Union, Tuple, List

from pykechain.exceptions import IllegalArgumentError
from pykechain.models import Property, Base
from pykechain.models.base import BaseInScope
from pykechain.models.input_checks import check_list_of_base, check_base
from pykechain.models.value_filter import BaseFilter


class _ReferenceProperty(Property):
    """
    Private base class for the KE-chain reference properties.

    .. versionadded:: 3.7
    :cvar REFERENCED_CLASS: handle to the Pykechain class that is referenced using this ReferenceProperty class.
    """

    REFERENCED_CLASS: type(Base) = Base

    def __init__(self, json, **kwargs):
        """Construct a ReferenceProperty from a json object."""
        super().__init__(json, **kwargs)

        self._cached_values = None

    @property
    def value(self) -> Optional[List[REFERENCED_CLASS]]:
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
        value = self.serialize_value(value)
        if self.use_bulk_update:
            self._pend_update(dict(value=value))
            self._value = (
                [dict(id=pk) for pk in value] if isinstance(value, list) else None
            )
            self._cached_values = None
        else:
            self._put_value(value)

    def value_ids(self) -> Optional[List[str]]:
        """
        Retrieve the referenced object UUIDs only.

        :return: list of UUIDs
        :rtype list
        """
        return [value.get("id") for value in self._value] if self.has_value() else None

    def _validate_values(self) -> List[str]:
        """
        Check if the `_value` attribute has valid content.

        :return list of UUIDs:
        :rtype list
        """
        if not self._value:
            return []

        object_ids = []
        for value in self._value:
            if isinstance(value, dict) and "id" in value:
                object_ids.append(str(value.get("id")))
            elif isinstance(value, (int, str)):
                object_ids.append(str(value))
            else:  # pragma: no cover
                raise ValueError(
                    f'Value "{value}" must be a dict with field `id` or a UUID.'
                )
        return object_ids

    @abstractmethod
    def _retrieve_objects(self, **kwargs) -> List[Base]:
        """
        Retrieve a list of Pykechain objects, type depending on the reference property type.

        This method is abstract because the exact retrieval method of the Client class changes per subclass.

        :param kwargs: optional arguments
        :return: list of Pykechain objects inheriting from Base
        """
        pass  # pragma: no cover

    def serialize_value(self, value: Union[Base, List, Tuple]) -> Optional[List[str]]:
        """
        Serialize the value to be set on the property by checking for a list of Base objects.

        :param value: non-serialized value
        :type value: Any
        :return: serialized value
        """
        try:
            value = check_base(value, cls=self.REFERENCED_CLASS, key="Reference")
            return [value] if value is not None else value
        except IllegalArgumentError:
            # expected to fail, as value should be an iterable
            return check_list_of_base(
                value, cls=self.REFERENCED_CLASS, key="references"
            )

    def set_prefilters(
        self,
        prefilters: Optional[List[BaseFilter]] = None,
        clear: Optional[bool] = False,
    ):
        """
        Set the prefilters on the reference property.

        :return: None
        """
        raise NotImplementedError(f"Method not (yet) implemented for {self.__class__}")

    def get_prefilters(self):
        """
        Get the prefilters currently on the reference property.

        :return: list of filter values.
        """
        raise NotImplementedError(f"Method not (yet) implemented for {self.__class__}")


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
        if self._options and "scope_id" not in self._options:
            # See whether the referenced model is an object with an ID
            if isinstance(referenced_object, self.REFERENCED_CLASS):
                x_scope_id = referenced_object.scope_id
            else:
                # retrieve the scope_id from the property model's value (which is an object in a scope (x_scope))
                referenced_models = self.model().value
                if not referenced_models or not isinstance(
                    referenced_models[0], self.REFERENCED_CLASS
                ):
                    # if the referenced model is not set or the referenced value is not in current scope
                    x_scope_id = self.scope_id
                else:
                    # get the scope_id from the referenced model
                    x_scope_id = referenced_models[0].scope_id
            self._options["scope_id"] = x_scope_id

            # edit the model of the property, such that all instances are updated as well.
            self.model().edit(options=self._options)
