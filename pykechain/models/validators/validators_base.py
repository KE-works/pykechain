from jsonschema import validate

from pykechain.enums import PropertyVTypes, ValidatorEffectTypes
from pykechain.models.validators.validator_schemas import validator_jsonschema_stub, effects_jsonschema_stub


class BaseValidator(object):
    jsonschema = None

    def __init__(self, json=None, *args, **kwargs):
        self._json = json or dict()
        self._config = self._json.get('config', dict())

    def as_json(self):
        self._json['config'] = self._config
        return self._json

    def validate_json(self):
        """validates the json representation of the validator against the validator jsonschema"""
        return validate(self.as_json(), self.jsonschema)


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
        self._obj = None

    def as_json(self):
        """Parses the validator to a proper validator json"""
        self._json['config'] = self._config
        return self._json

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
    def parse(cls, json: dict):
        """Parses the json and creates the proper ProperyValidator"""
        if 'vtype' in json:
            vtype = json.get('vtype')
            if vtype not in PropertyVTypes.values():
                raise Exception("Validator unknown, incorrect json: '{}'".format(json))

            from pykechain.models import validators
            vtype_implementation_classname = vtype[0].upper() + vtype[1:]
            if hasattr(validators, vtype_implementation_classname):
                return getattr(validators, vtype_implementation_classname)(json=json)
            else:
                raise Exception('unknown vtype in json')
        raise Exception("Validator unknown, incorrect json: '{}'".format(json))

    @property
    def is_valid(self):
        if not self._validation_result:
            self.logic(self._obj)
        return self._validation_result

    @property
    def is_invalid(self):
        if not self._validation_result:
            self.logic(self._obj)
        return not self._validation_result

    def logic(self, obj=None):
        self._validation_result = True
        return self._validation_result

    def __call__(self, obj):
        return self.logic(obj)


class ValidatorEffect(BaseValidator):
    effect = ValidatorEffectTypes.NONE_EFFECT
    jsonschema = effects_jsonschema_stub

    def __init__(self, json=None, *args, **kwargs):
        super(ValidatorEffect, self).__init__(json=json, *args, **kwargs)
        self._json = json or {'effect': self.effect, 'config': {}}

    def as_json(self):
        return self._json

    def __call__(self, **kwargs):
        return True

    @classmethod
    def parse(cls, json):
        effect = json.get('effect')
        if effect:
            from pykechain.models import validators
            effect_implementation_classname = effect[0].upper() + effect[1:]
            if hasattr(validators, effect_implementation_classname):
                return getattr(validators, effect_implementation_classname)(json=json)
            else:
                raise Exception('unknown effect in json')
        raise Exception("Effect unknown, incorrect json: '{}'".format(json))
