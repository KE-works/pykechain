from typing import Any, AnyStr, Union, Tuple, Dict  # flake8: noqa # pylint: disable=unused-import

from jsonschema import validate

from pykechain.enums import PropertyVTypes, ValidatorEffectTypes
from pykechain.models.validators.validator_schemas import validator_jsonschema_stub, effects_jsonschema_stub


class BaseValidator(object):
    """Base class for all Validators.

    This is the base implementation for both the :class:`PropertyValidator` as well as the :class:`ValidatorEffect`.

    .. versionadded:: 2.2

    :cvar jsonschema: jsonschema to validate the json representation of the Validator
    :type jsonschema: dict
    :cvar accuracy: default value used in comparison of floats, normally 1E-6
    :type accuracy: float
    """

    jsonschema = None  # type: Union[Dict, None]
    accuracy = 1E-6

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
        # type: (dict) -> Any
        """Parse a json dict and return the correct subclass."""
        raise NotImplementedError


class PropertyValidator(BaseValidator):
    """Base class for all property validators.

    If json is provided, the validator is instantiated based on that json.

    .. versionadded:: 2.2

    :cvar vtype: Validator type, one of :class:`pykechain.enums.PropertyVTypes`
    :type vtype: basestring
    :cvar jsonschema: jsonschema to validate the structure of the json representation of the effect against
    :type jsonschema: dict
    """

    vtype = PropertyVTypes.NONEVALIDATOR  # type: str
    jsonschema = validator_jsonschema_stub

    def __init__(self, json=None, *args, **kwargs):
        """Construct a Property Validator."""
        super(PropertyValidator, self).__init__(json=json, *args, **kwargs)
        self._json = json or {'vtype': self.vtype, 'config': {}}
        self._validation_result = None
        self._validation_reason = None
        self._value = None

        if self._config.get('on_valid'):
            self.on_valid = self._parse_effects(self._config.get('on_valid'))
        else:
            self.on_valid = kwargs.get('on_valid') or []

        if self._config.get('on_invalid'):
            self.on_invalid = self._parse_effects(self._config.get('on_invalid'))
        else:
            self.on_invalid = kwargs.get('on_invalid') or []

    def _parse_effects(self, effects_json=None):
        # type: (dict) -> Any
        """Parse multiple effects from an effects(list) json."""
        if isinstance(effects_json, list):
            return [ValidatorEffect.parse(effect) for effect in effects_json]
        elif isinstance(effects_json, dict):
            return ValidatorEffect.parse(effects_json)
        else:
            raise Exception("The provided json, should be a list of valid effects, "
                            "or a single effect. Got '{}'".format(effects_json))

    @classmethod
    def parse(cls, json):
        # type: (Dict) -> Any
        """Parse a json dict and return the correct subclass of :class:`PropertyValidator`.

        It uses the 'effect' key to determine which :class:`PropertyValidator` to instantiate.
        Please refer to :class:`pykechain.enums.PropertyVTypes` for the supported effects.

        :param json: dictionary containing the specific keys to parse into a :class:`PropertyValidator`
        :type json: dict
        :returns: the instantiated subclass of :class:`PropertyValidator`
        :rtype: :class:`PropertyValidator` or subclass thereof
        """
        if 'vtype' in json:
            vtype = json.get('vtype')
            if vtype not in PropertyVTypes.values():
                raise Exception("Validator unknown, incorrect json: '{}'".format(json))

            from pykechain.models.validators import validators
            vtype_implementation_classname = "{}{}".format(vtype[0].upper(), vtype[1:])  # type: ignore
            if hasattr(validators, vtype_implementation_classname):
                return getattr(validators, vtype_implementation_classname)(json=json)
            else:
                raise Exception('unknown vtype in json')
        raise Exception("Validator unknown, incorrect json: '{}'".format(json))

    def as_json(self):
        # type: () -> dict
        """JSON representation of the effect.

        :returns: a python dictionary, serializable as json of the effect
        :rtype: dict
        """
        new_json = dict(
            vtype=self.vtype,
            config=self._config
        )

        if self.on_valid:
            new_json['config']['on_valid'] = [effect.as_json() for effect in self.on_valid]
        if self.on_invalid:
            new_json['config']['on_invalid'] = [effect.as_json() for effect in self.on_invalid]

        self._json = new_json
        return self._json

    def __call__(self, value):
        # type: (Any) -> bool
        """Trigger the validation of the validator.

        The reason may retrieved by the :func:`get_reason()` method.

        :param value: The value to check against
        :type value: Any
        :return: bool
        """
        self._logic(value)

        if self._validation_result is not None and self._validation_result:
            for effect in self.on_valid:
                effect()
        elif self._validation_result is not None and not self._validation_result:
            for effect in self.on_invalid:
                effect()

        return self._validation_result

    def is_valid(self, value):
        # type: (Any) -> bool
        """Check if the validation against a value, returns a boolean.

        This is the logical inverse of the :func:`is_invalid()` method.

        :param value: The value to check against
        :type value: Any
        :return: True if valid, False if invalid
        :rtype: bool
        """
        return self.__call__(value)

    def is_invalid(self, value):
        # type: (Any) -> bool
        """Check if the validation against a value, returns a boolean.

        This is the logical inverse of the :func:`is_valid()` method.

        :param value: The value to check against
        :type value: Any
        :return: True if INvalid, False if valid
        :rtype: bool
        """
        return not self.is_valid(value)

    def get_reason(self):
        # type: () -> AnyStr
        """Retrieve the reason of the (in)validation.

        :return: reason text
        :rtype: basestring
        """
        return self._validation_reason

    def _logic(self, value=None):
        # type: (Any) -> Tuple[Union[bool, None], str]
        """Process the inner logic of the validator.

        The validation results are returned as tuple (boolean (true/false), reasontext)
        """
        self._validation_result, self._validation_reason = None, 'No reason'
        return self._validation_result, self._validation_reason


class ValidatorEffect(BaseValidator):
    """
    A Validator Effect.

    This is an effect that can be associated with the :attr:`PropertyValidator.on_valid` or
    :attr:`PropertyValidator.on_invalid`. The effects associated are called based on the results of the
    validation of the :class:`PropertyValidator`.

    .. versionadded:: 2.2

    :cvar effect: Effect type, one of :class:`pykechain.enums.ValidatorEffectTypes`
    :cvar jsonschema: jsonschema to validate the structure of the json representation of the effect against
    """

    effect = ValidatorEffectTypes.NONE_EFFECT
    jsonschema = effects_jsonschema_stub

    def __init__(self, json=None, *args, **kwargs):
        """Construct a Validator Effect."""
        super(ValidatorEffect, self).__init__(json=json, *args, **kwargs)
        self._json = json or {'effect': self.effect, 'config': {}}

    def __call__(self, **kwargs):
        """Execute the effect."""
        return True

    @classmethod
    def parse(cls, json):
        # type: (dict) -> Any
        """Parse a json dict and return the correct subclass of :class:`ValidatorEffect`.

        It uses the 'effect' key to determine which :class:`ValidatorEffect` to instantiate.
        Please refer to :class:`enums.ValidatorEffectTypes` for the supported effects.

        :param json: dictionary containing the specific keys to parse into a :class:`ValidatorEffect`
        :type json: dict
        :returns: the instantiated subclass of :class:`ValidatorEffect`
        :rtype: :class:`ValidatorEffect` or subclass
        """
        effect = json.get('effect')
        if effect:
            from pykechain.models.validators import effects
            effect_implementation_classname = effect[0].upper() + effect[1:]
            if hasattr(effects, effect_implementation_classname):
                return getattr(effects, effect_implementation_classname)(json=json)
            else:
                raise Exception('unknown effect in json')
        raise Exception("Effect unknown, incorrect json: '{}'".format(json))

    def as_json(self):
        # type: () -> dict
        """JSON representation of the effect.

        :returns: a python dictionary, serializable as json of the effect
        :rtype: dict
        """
        self._json = dict(
            effect=self.effect,
            config=self._config
        )
        return self._json
