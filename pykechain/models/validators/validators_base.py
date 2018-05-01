from jsonschema import validate

from pykechain.enums import PropertyVTypes, ValidatorEffectTypes
from pykechain.models.validators.validator_schemas import validator_jsonschema_stub, effects_jsonschema_stub


class BaseValidator(object):
    jsonschema = None

    def __init__(self, json=None, *args, **kwargs):
        self._json = json or dict(config=dict())
        self._config = self._json.get('config', dict())

    def as_json(self):
        """Parses the validator to a proper validator json"""
        return self._json

    def validate_json(self):
        """validates the json representation of the validator against the validator jsonschema"""
        return validate(self._json, self.jsonschema)

    @classmethod
    def parse(cls, json):
        raise NotImplementedError


class PropertyValidator(BaseValidator):
    """Base class for all validators

    If json is provided, the validator is instantiated based on that json.
    """
    vtype = PropertyVTypes.NONEVALIDATOR
    jsonschema = validator_jsonschema_stub

    def __init__(self, json=None, *args, **kwargs):
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
        """Parses multiple effects from an effects(list) json"""
        if isinstance(effects_json, list):
            return [ValidatorEffect.parse(effect) for effect in effects_json]
        elif isinstance(effects_json, dict):
            return ValidatorEffect.parse(effects_json)
        else:
            raise Exception("The provided json, should be a list of valid effects, "
                            "or a single effect. Got '{}'".format(effects_json))

    @classmethod
    def parse(cls, json):
        """Parses the json and creates the proper ProperyValidator"""
        if 'vtype' in json:
            vtype = json.get('vtype')
            if vtype not in PropertyVTypes.values():
                raise Exception("Validator unknown, incorrect json: '{}'".format(json))

            from pykechain.models.validators import validators
            vtype_implementation_classname = vtype[0].upper() + vtype[1:]
            if hasattr(validators, vtype_implementation_classname):
                return getattr(validators, vtype_implementation_classname)(json=json)
            else:
                raise Exception('unknown vtype in json')
        raise Exception("Validator unknown, incorrect json: '{}'".format(json))

    def as_json(self):
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
        """This will trigger the validation of the validator.

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
        """Checks if the validation against a value, returns a boolean.

        This is the logical inverse of the :func:`is_invalid()` method.

        :param value: The value to check against
        :type value: Any
        :return: True if valid, False if invalid
        :rtype: bool
        """
        return self.__call__(value)

    def is_invalid(self, value):
        """Checks if the validation against a value, returns a boolean.

        This is the logical inverse of the :func:`is_valid()` method.

        :param value: The value to check against
        :type value: Any
        :return: True if INvalid, False if valid
        :rtype: bool
        """
        return not self.is_valid(value)

    def get_reason(self):
        """Retrieves the reason of the (in)validation.

        :return: reason text
        :rtype: basestring
        """
        return self._validation_reason

    def _logic(self, value=None):
        """Process the inner logic of the validator.

        The validation results are returned as tuple (boolean (true/false), reasontext)
        """
        self._validation_result, self._validation_reason = None, 'No reason'


class ValidatorEffect(BaseValidator):
    effect = ValidatorEffectTypes.NONE_EFFECT
    jsonschema = effects_jsonschema_stub

    def __init__(self, json=None, *args, **kwargs):
        super(ValidatorEffect, self).__init__(json=json, *args, **kwargs)
        self._json = json or {'effect': self.effect, 'config': {}}

    def __call__(self, **kwargs):
        return True

    @classmethod
    def parse(cls, json):
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
        self._json = dict(
            effect=self.effect,
            config=self._config
        )
        return self._json
