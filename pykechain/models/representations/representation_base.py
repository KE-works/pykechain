from typing import Dict

from jsonschema import validate

from pykechain.enums import PropertyRepresentation
from pykechain.models.validators.validator_schemas import representation_jsonschema_stub


class BaseRepresentation(object):
    """
    Base class for all Representations.

    :cvar jsonschema: jsonschema to validate the json representation of the Validator
    :type jsonschema: dict
    """

    jsonschema = representation_jsonschema_stub

    def __init__(self, json=None, *args, **kwargs):
        """Construct a base validator."""
        self._json = json or dict(config=dict())
        self._config = self._json.get('config', dict())

    def as_json(self):
        # type: () -> dict
        """Parse the validator to a proper validator json."""
        return self._json

    def validate_json(self):
        # type: () -> Any
        """Validate the json representation of the validator against the validator jsonschema."""
        return validate(self._json, self.jsonschema)

    @classmethod
    def parse(cls, json):
        # type: (Dict) -> BaseRepresentation
        """Parse a json dict and return the correct subclass of :class:`BaseRepresentation`.

        It uses the 'effect' key to determine which :class:`BaseRepresentation` to instantiate.
        Please refer to :class:`pykechain.enums.PropertyRepresentation` for the supported representations.

        :param json: dictionary containing the specific keys to parse into a :class:`BaseRepresentation`
        :type json: dict
        :returns: the instantiated subclass of :class:`BaseRepresentation`
        :rtype: :class:`BaseRepresentation` or subclass thereof
        """
        if 'rtype' in json:
            rtype = json.get('rtype')
            if rtype not in PropertyRepresentation.values():
                raise Exception("Representation unknown, incorrect json: '{}'".format(json))

            from pykechain.models.validators import validators
            rtype_implementation_classname = "{}{}".format(rtype[0].upper(), rtype[1:])  # type: ignore
            if hasattr(validators, rtype_implementation_classname):
                return getattr(validators, rtype_implementation_classname)(json=json)
            else:
                raise Exception('unknown rtype in json')
        raise Exception("Representation unknown, incorrect json: '{}'".format(json))
