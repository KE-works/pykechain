# Validators for the properties
# live in Property.options; which is a json field array
from math import inf

from pykechain.models.validators.validators_base import PropertyValidator, ValidatorEffect
from pykechain.enums import PropertyVTypes, ValidatorEffectTypes


class NumericRangeValidator(PropertyValidator):
    vtype = PropertyVTypes.NUMERICRANGE

    def __init__(self, json=None, minvalue=None, maxvalue=None, stepsize=None, enforce_stepsize=False, **kwargs):
        super(NumericRangeValidator, self).__init__(json=json, **kwargs)

        self.minvalue = minvalue or self._config.get('minvalue') or -inf
        self.maxvalue = maxvalue or self._config.get('maxvalue') or inf
        self.stepsize = stepsize or self._config.get('stepsize') or 1
        self.enforce_stepsize = enforce_stepsize or self._config.get('enforce_stepsize') or False

        if self._config.get('on_valid'):
            self.on_valid = self._parse_effects(self._config.get('on_valid'))
        else:
            self.on_valid = kwargs.get('on_valid') or []

        if self._config.get('on_invalid'):
            self.on_invalid = self._parse_effects(self._config.get('on_invalid'))
        else:
            self.on_invalid = kwargs.get('on_invalid') or []

        self._obj = None
        self._validation_result = None

    def logic(self, obj=None):
        if obj.value:
            self._validation_result = obj.value >= self.minvalue and obj.value <= self.maxvalue
        if self.stepsize != 1 and self.enforce_stepsize:
            self._validation_result = (obj.value - self.maxvalue) % self.stepsize == 0

        if self._validation_result is True:
            for effect in self.on_valid:
                effect()

        if self._validation_result is False:
            for effect in self.on_invalid:
                effect()


class RequiredFieldValidator(PropertyValidator):
    vtype = PropertyVTypes.REQUIREDFIELD


class BooleanFieldValidator(PropertyValidator):
    vtype = PropertyVTypes.BOOLEANFIELD


class EvenNumberValidator(PropertyValidator):
    vtype = PropertyVTypes.EVENNUMBER


class OddNumberValidator(PropertyValidator):
    vtype = PropertyVTypes.ODDNUMBER


#
# Text Effects
#

class TextEffect(ValidatorEffect):
    effect = ValidatorEffectTypes.TEXT_EFFECT


class ErrorTextEffect(ValidatorEffect):
    """A Errortext effect, that will set a text"""
    effect = ValidatorEffectTypes.ERRORTEXT_EFFECT

    def __init__(self, json=None, text="The validation resulted in an error.", **kwargs):
        super(ErrorTextEffect, self).__init__(json=json, **kwargs)
        self.text = text

    def as_json(self):
        self._config['text'] = self.text
        return self._json


class HelpTextEffect(ValidatorEffect):
    """A Errortext effect, that will set a text"""
    effect = ValidatorEffectTypes.HELPTEXT_EFFECT

    def __init__(self, json=None, text="", **kwargs):
        super(HelpTextEffect, self).__init__(json=json, **kwargs)
        self.text = text

    def as_json(self):
        self._config['text'] = self.text
        return self._json


#
# Apply Visual Style Effects
#

class VisualEffect(ValidatorEffect):
    """A visualeffect, to be processed by the frontend

    :ivar applyCss: css class to apply in case of this effect
    """
    effect = ValidatorEffectTypes.VISUALEFFECT

    def __init__(self, json=None, applyCss=None, **kwargs):
        super(VisualEffect, self).__init__(json=json, **kwargs)
        self.applyCss = applyCss or self._config.get('applyCss')

    def as_json(self):
        self._config['applyCss'] = self.applyCss
        self._json['config'] = self._config
        return self._json


class ValidVisualEffect(VisualEffect):
    def __init__(self, json=None, applyCss='valid'):
        super(__class__, self).__init__(json=json, applyCss=applyCss)


class InvalidVisualEffect(VisualEffect):
    def __init__(self, json=None, applyCss='invalid'):
        super(__class__, self).__init__(json=json, applyCss=applyCss)
