import warnings
from abc import abstractmethod
from typing import Any, Dict

from jsonschema import validate

from pykechain.models.validators.validator_schemas import representation_jsonschema_stub


class BaseRepresentation:
    """
    Base class for all Representations.

    :cvar jsonschema: jsonschema to validate the json of the representation
    :cvar rtype: type of representation
    """

    jsonschema = representation_jsonschema_stub
    rtype = None
    _config_value_key = None

    def __init__(self, obj=None, json=None, value=None, prop=None):
        """
        Construct a base representation.

        :param obj: the object to which the representation is applied, such as a property.
        :param json: representation json (usually part of the original object json)
        :param value: value of the representation, its options vary per representation type
        :param prop: deprecated keyword for obj
        """
        if prop is not None:
            warnings.warn(
                "Keyword `prop` is deprecated in favor of `obj`.",
                PendingDeprecationWarning,
            )
            obj = prop
            del prop

        self._obj = obj
        self._json: dict = json or dict(rtype=self.rtype, config=dict())

        self._config: dict = self._json.get("config", dict())
        self._json["config"] = self._config

        if value is not None:
            self.validate_representation(value)
            self._config[self._config_value_key] = value

    def __repr__(self):
        return f"{self.__class__.__name__} ({self.value})"

    def as_json(self) -> Dict:
        """Parse the validator to a proper validator json."""
        return self._json

    def validate_json(self) -> Any:
        """Validate the json representation of the validator against the validator jsonschema."""
        return validate(self._json, self.jsonschema)

    @classmethod
    def parse(cls, obj: Any, json: Dict) -> "BaseRepresentation":
        """Parse a json dict and return the correct subclass of :class:`BaseRepresentation`.

        It uses the 'rtype' key to determine which :class:`BaseRepresentation` to instantiate.

        :param obj: object to which the `BaseRepresentation` belongs.
        :param json: dictionary containing the specific keys to parse into a :class:`BaseRepresentation`
        :returns: the instantiated subclass of :class:`BaseRepresentation`
        """
        try:
            rtype = json["rtype"]
        except KeyError:
            raise ValueError(
                f"Representation unknown, incorrect json: '{json}'"
            )
        try:
            from pykechain.models.representations import rtype_class_map

            repr_class: type(BaseRepresentation) = rtype_class_map[rtype]
        except KeyError:
            raise TypeError(f'Unknown rtype "{rtype}" in json')

        return repr_class(obj=obj, json=json)

    @property
    def value(self):
        """
        Retrieve current representation value.

        :return: value
        """
        return self._config[self._config_value_key] if self._config_value_key else None

    @value.setter
    def value(self, value):
        """
        Set a new representation value.

        :param value: the new value to be set
        :return: the value
        """
        self.validate_representation(value)
        self._config[self._config_value_key] = value

        # Update the property in-place
        if self._obj:
            self._obj.representations = self._obj.representations

    @abstractmethod
    def validate_representation(self, value: Any) -> None:
        """
        Validate whether the representation value can be set.

        :param value: representation value to set.
        :raises IllegalArgumentError
        :return: None
        """
        pass  # pragma: no cover
