# Validators for the properties
# live in Property.options; which is a json field array
import re
from math import inf

from pykechain.enums import PropertyVTypes
from pykechain.models.validators.validators_base import PropertyValidator


class NumericRangeValidator(PropertyValidator):
    vtype = PropertyVTypes.NUMERICRANGE

    def __init__(self, json=None, minvalue=None, maxvalue=None, stepsize=None, enforce_stepsize=None, **kwargs):
        super(NumericRangeValidator, self).__init__(json=json, **kwargs)

        if minvalue is not None:
            self._config['minvalue'] = minvalue
        if maxvalue is not None:
            self._config['maxvalue'] = maxvalue
        if stepsize is not None:
            self._config['stepsize'] = stepsize
        if enforce_stepsize is not None:
            self._config['enforce_stepsize'] = enforce_stepsize

        self.minvalue = self._config.get('minvalue', -inf)
        self.maxvalue = self._config.get('maxvalue', inf)
        self.stepsize = self._config.get('stepsize', None)
        self.enforce_stepsize = self._config.get('enforce_stepsize', None)

    def _logic(self, value=None):
        basereason = "Value '{}' should be between {} and {}".format(value, self.minvalue, self.maxvalue)
        self._validation_result, self._validation_reason = None, None

        if value is not None:
            self._validation_result = value >= self.minvalue and value <= self.maxvalue
            if not self._validation_result:
                self._validation_reason = basereason
            else:
                self._validation_reason = basereason.replace('should be', 'is')

        if self.stepsize != 1 and self.enforce_stepsize:
            # to account also for floating point stepsize checks: https://stackoverflow.com/a/30445184/246235
            if self.minvalue == -inf:
                self._validation_result = abs(value/self.stepsize -
                                              round(value/self.stepsize)) < 1E-6
            else:
                self._validation_result = abs((value-self.minvalue)/self.stepsize -
                                              round((value-self.minvalue)/self.stepsize)) < 1E-6

            if not self._validation_result:
                self._validation_reason = "Value '{}' is not in alignment with a stepsize of {}". \
                    format(value, self.stepsize)

        return self._validation_result, self._validation_reason


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

        self.pattern = pattern or self._config.get('pattern', r'.*')
        self._re = re.compile(self.pattern)

    def _logic(self, value=None):
        if value is None:
            return None, None

        basereason = "Value '{}' should match the regex pattern '{}'".format(value, self.pattern)

        self._validation_result = re.match(self._re, value)
        if not self._validation_result:
            self._validation_reason = basereason

        return self._validation_result, self._validation_reason
