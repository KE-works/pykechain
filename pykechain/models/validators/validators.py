# Validators for the properties
# live in Property.options; which is a json field array
import re
from math import inf

from pykechain.enums import PropertyVTypes
from pykechain.models.validators.validators_base import PropertyValidator


class NumericRangeValidator(PropertyValidator):
    vtype = PropertyVTypes.NUMERICRANGE

    def __init__(self, json=None, minvalue=None, maxvalue=None, stepsize=None, enforce_stepsize=False, **kwargs):
        super(NumericRangeValidator, self).__init__(json=json, **kwargs)

        self.minvalue = minvalue or self._config.get('minvalue', -inf)
        self.maxvalue = maxvalue or self._config.get('maxvalue', inf)
        self.stepsize = stepsize or self._config.get('stepsize', None)
        self.enforce_stepsize = enforce_stepsize or self._config.get('enforce_stepsize') or False

        if self._config.get('on_valid'):
            self.on_valid = self._parse_effects(self._config.get('on_valid'))
        else:
            self.on_valid = kwargs.get('on_valid') or []

        if self._config.get('on_invalid'):
            self.on_invalid = self._parse_effects(self._config.get('on_invalid'))
        else:
            self.on_invalid = kwargs.get('on_invalid') or []

    def __call__(self, value):
        return self.logic(value)

    def logic(self, value=None):
        if value is not None:
            self._validation_result = value >= self.minvalue and value <= self.maxvalue
        else:
            return None
        if self.stepsize != 1 and self.enforce_stepsize:
            self._validation_result = (value - self.maxvalue) % self.stepsize == 0

        if self._validation_result is True:
            for effect in self.on_valid:
                effect()

        if self._validation_result is False:
            for effect in self.on_invalid:
                effect()

        return self._validation_result


class RequiredFieldValidator(PropertyValidator):
    vtype = PropertyVTypes.REQUIREDFIELD


class BooleanFieldValidator(PropertyValidator):
    vtype = PropertyVTypes.BOOLEANFIELD


class EvenNumberValidator(PropertyValidator):
    vtype = PropertyVTypes.EVENNUMBER


class OddNumberValidator(PropertyValidator):
    vtype = PropertyVTypes.ODDNUMBER

class RegexStringValidator(PropertyValidator):
    vtype = PropertyVTypes.REGEXSTRING

    def __init__(self, json=None, pattern=None, **kwargs):
        super(RegexStringValidator, self).__init__(json=json, **kwargs)

        self._pattern = pattern or self._config.get('pattern', None)
        self._re = re.compile(self._pattern)

    def logic(self, value=None):
        re.match(self._re, value)