from abc import abstractmethod
from typing import Dict, Any
from jsonschema import validate

from pykechain.enums import PropertyRepresentation
from pykechain.models.validators.validator_schemas import representation_jsonschema_stub


class BaseRepresentation(object):
    """
    Base class for all Representations.

    :cvar jsonschema: jsonschema to validate the json representation of the Validator
    :type jsonschema: Dict
    :cvar rtype: type of representation
    :type rtype: Text
    """

    jsonschema = representation_jsonschema_stub
    rtype = None
    _config_value_key = None

    def __init__(self, prop, json=None, value=None):
        """Construct a base validator."""
        self._property = prop

        self._json = json or dict(rtype=self.rtype, config=dict())  # type: dict

        self._config = self._json.get('config', dict())  # type: dict

        if value is None and self._config_value_key in self._config:
            self._value = self._config[self._config_value_key]
        else:
            self.validate_representation(value)
            self._config[self._config_value_key] = value
            self._value = value

    def as_json(self):
        # type: () -> dict
        """Parse the validator to a proper validator json."""
        return self._json

    def validate_json(self):
        # type: () -> Any
        """Validate the json representation of the validator against the validator jsonschema."""
        return validate(self._json, self.jsonschema)

    @classmethod
    def parse(cls, prop, json):
        # type: (AnyProperty, Dict) -> BaseRepresentation
        """Parse a json dict and return the correct subclass of :class:`BaseRepresentation`.

        It uses the 'effect' key to determine which :class:`BaseRepresentation` to instantiate.
        Please refer to :class:`pykechain.enums.PropertyRepresentation` for the supported representations.

        :param prop: Property object to which the `BaseRepresentation` belongs.
        :type: prop: AnyProperty
        :param json: dictionary containing the specific keys to parse into a :class:`BaseRepresentation`
        :type json: dict
        :returns: the instantiated subclass of :class:`BaseRepresentation`
        :rtype: :class:`BaseRepresentation` or subclass thereof
        """
        if 'rtype' in json:
            rtype = json.get('rtype')
            if rtype not in PropertyRepresentation.values():
                raise Exception("Representation unknown, incorrect json: '{}'".format(json))

            from pykechain.models.representations import representations
            rtype_implementation_classname = "{}{}".format(rtype[0].upper(), rtype[1:])  # type: ignore
            if hasattr(representations, rtype_implementation_classname):
                return getattr(representations, rtype_implementation_classname)(prop=prop, json=json)
            else:
                raise Exception('unknown rtype in json')
        raise Exception("Representation unknown, incorrect json: '{}'".format(json))

    @property
    def value(self):
        """
        Retrieve current representation value.

        :return: value
        :rtype Any
        """
        return self._value

    @value.setter
    def value(self, value):
        """
        Set a new representation value.

        :param value: the new value to be set
        :type value: Any
        :return: the value
        :rtype Any
        """
        self.validate_representation(value)

        self._value = value
        self._config[self._config_value_key] = value

        # Update the property in-place
        self._property.representations = self._property.representations

    @abstractmethod
    def validate_representation(self, value):
        # type: (Any) -> None
        """
        Validate whether the representation value can be set.

        :param value: representation value to set.
        :type value: Any
        :raises IllegalArgumentError
        :return: None
        """
        pass
