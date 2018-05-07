from __future__ import division

import re

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

        self.minvalue = self._config.get('minvalue', float('-inf'))
        self.maxvalue = self._config.get('maxvalue', float('inf'))
        self.stepsize = self._config.get('stepsize', None)
        self.enforce_stepsize = self._config.get('enforce_stepsize', None)

        if self.minvalue > self.maxvalue:
            raise Exception('The minvalue ({}) should be smaller than the maxvalue ({}) of the numeric '
                            'range validation'.format(self.minvalue, self.maxvalue))
        if self.enforce_stepsize and self.stepsize is None:
            raise Exception('The stepsize should be provided when enforcing stepsize')

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
            if self.minvalue == float('-inf'):
                self._validation_result = abs(value / self.stepsize -
                                              round(value / self.stepsize)) < 1E-6
            else:
                self._validation_result = abs((value - self.minvalue) / self.stepsize -
                                              round((value - self.minvalue) / self.stepsize)) < 1E-6

            if not self._validation_result:
                self._validation_reason = "Value '{}' is not in alignment with a stepsize of {}". \
                    format(value, self.stepsize)

        return self._validation_result, self._validation_reason


class RequiredFieldValidator(PropertyValidator):
    vtype = PropertyVTypes.REQUIREDFIELD

    def _logic(self, value=None):
        basereason = "Value is required"
        self._validation_result, self._validation_reason = None, None

        if value is not None and value != '':
            self._validation_result = True
            self._validation_reason = "Value is provided"
        else:
            self._validation_result = False
            self._validation_reason = basereason

        return self._validation_result, self._validation_reason


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

        if pattern is not None:
            self._config['pattern'] = pattern

        self.pattern = self._config.get('pattern', r'.*')
        self._re = re.compile(self.pattern)

    def _logic(self, value=None):
        if value is None:
            return None, None

        basereason = "Value '{}' should match the regex pattern '{}'".format(value, self.pattern)

        self._validation_result = re.match(self._re, value)
        if not self._validation_result:
            self._validation_reason = basereason
        else:
            self._validation_reason = basereason.replace('should match', 'matches')

        return self._validation_result, self._validation_reason
