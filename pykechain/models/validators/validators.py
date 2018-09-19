from __future__ import division

import re
from typing import Any, Union, Tuple  # flake8: noqa # pylint: disable=unused-import

from pykechain.enums import PropertyVTypes
from pykechain.models.validators.validators_base import PropertyValidator


class NumericRangeValidator(PropertyValidator):
    """
    A numeric range validator, which validates a number between a range.

    The range validates positively upto and **including** the minvalue and maxvalue.

    An added ability is the check if the number conforms to a step within that range.
    The validation checks for both integer and floats. The stepsize is only enforced when the :attr:`enforce_stepsize`
    is set to `True`. This enforcement is accurate to an accuracy set in the :const:`.accuracy`
    (normally set to be 1E-6).

    .. versionadded:: 2.2

    :ivar minvalue: minimum value of the range
    :type minvalue: float or int
    :ivar maxvalue: maximum value of the range
    :type maxvalue: float or int
    :ivar stepsize: stepsize
    :type stepsize: float or int
    :ivar enforce_stepsize: flag to ensure that the stepsize is enforced
    :type enforce_stepsize: bool

    Examples
    --------
    >>> validator = NumericRangeValidator(minvalue=0, maxvalue=50)
    >>> validator.is_valid(42)
    True
    >>> validator.is_valid(50)
    True
    >>> validator.is_valid(50.0001)
    False
    >>> validator.is_valid(-1)
    False
    >>> validator.get_reason()
    Value '-1' should be between 0 and 50

    >>> stepper = NumericRangeValidator(stepsize=1000, enforce_stepsize=True)
    >>> stepper.is_valid(2000)
    True

    """

    vtype = PropertyVTypes.NUMERICRANGE

    def __init__(self, json=None, minvalue=None, maxvalue=None, stepsize=None, enforce_stepsize=None, **kwargs):
        """Construct the numeric range validator."""
        super(NumericRangeValidator, self).__init__(json=json, **kwargs)

        if minvalue is not None:
            self._config['minvalue'] = minvalue
        if maxvalue is not None:
            self._config['maxvalue'] = maxvalue
        if stepsize is not None:
            self._config['stepsize'] = stepsize
        if enforce_stepsize is not None:
            self._config['enforce_stepsize'] = enforce_stepsize

        self.minvalue = float('-inf') if minvalue is None else minvalue
        self.maxvalue = float('inf') if maxvalue is None else maxvalue
        self.stepsize = self._config.get('stepsize', None)
        self.enforce_stepsize = self._config.get('enforce_stepsize', None)

        if self.minvalue > self.maxvalue:
            raise Exception('The minvalue ({}) should be smaller than the maxvalue ({}) of the numeric '
                            'range validation'.format(self.minvalue, self.maxvalue))
        if self.enforce_stepsize and self.stepsize is None:
            raise Exception('The stepsize should be provided when enforcing stepsize')

    def _logic(self, value=None):
        # type: (Any) -> Tuple[Union[bool, None], str]
        basereason = "Value '{}' should be between {} and {}".format(value, self.minvalue, self.maxvalue)
        self._validation_result, self._validation_reason = None, "No reason"

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
                                              round(value / self.stepsize)) < self.accuracy
            else:
                self._validation_result = abs((value - self.minvalue) / self.stepsize -
                                              round((value - self.minvalue) / self.stepsize)) < self.accuracy

            if not self._validation_result:
                self._validation_reason = "Value '{}' is not in alignment with a stepsize of {}". \
                    format(value, self.stepsize)

        return self._validation_result, self._validation_reason


class RequiredFieldValidator(PropertyValidator):
    """
    Required field validator ensures that a value is provided.

    Does validate all values. Does not validate `None` or `''` (empty string).

    .. versionadded:: 2.2

    Examples
    --------
    >>> validator = RequiredFieldValidator()
    >>> validator.is_valid("A value")
    True
    >>> validator.is_valid("")
    False
    >>> validator.is_valid(None)
    False
    >>> validator.get_reason()
    "Value is required"

    """

    vtype = PropertyVTypes.REQUIREDFIELD

    def _logic(self, value=None):
        # type: (Any) -> Tuple[Union[bool, None], str]
        basereason = "Value is required"
        self._validation_result, self._validation_reason = None, "No reason"

        if value is not None and value != '':
            self._validation_result = True
            self._validation_reason = "Value is provided"
        else:
            self._validation_result = False
            self._validation_reason = basereason

        return self._validation_result, self._validation_reason


class BooleanFieldValidator(PropertyValidator):
    """A boolean field validator.

    This is a stub implementation. Should validate if a value is either 'truthy' or 'falsy'.
    """

    vtype = PropertyVTypes.BOOLEANFIELD


class EvenNumberValidator(PropertyValidator):
    """An even number validator that validates `True` when the number is even.

    Even numbers are scalar numbers which can be diveded by 2 and return a scalar. Floating point numbers are converted
    to integer first. So `int(4.5)` = 4.

    .. versionadded:: 2.2

    Example
    -------
    >>> validator = EvenNumberValidator()
    >>> validator.is_valid(4)
    True
    >>> validator.is_valid(4.5)  # float is converted to integer first
    True

    """

    vtype = PropertyVTypes.EVENNUMBER

    def _logic(self, value=None):
        # type: (Any) -> Tuple[Union[bool, None], str]
        if value is None:
            self._validation_result, self.validation_reason = None, "No reason"
            return self._validation_result, self._validation_reason
        if not isinstance(value, (int, float)):
            self._validation_result, self.validation_reason = False, "Value should be an integer, or float (floored)"
            return self._validation_result, self._validation_reason

        basereason = "Value '{}' should be an even number".format(value)

        self._validation_result = int(value) % 2 < self.accuracy
        if self._validation_result:
            self._validation_reason = basereason.replace("should be", "is")
            return self._validation_result, self._validation_reason
        else:
            self._validation_reason = basereason
            return self._validation_result, self._validation_reason


class OddNumberValidator(PropertyValidator):
    """A odd number validator that validates `True` when the number is odd.

    Example
    -------
    >>> validator = OddNumberValidator()
    >>> validator.is_valid(3)
    True
    >>> validator.is_valid(3.5)  # float is converted to integer first
    True

    """

    vtype = PropertyVTypes.ODDNUMBER

    def _logic(self, value=None):
        # type: (Any) -> Tuple[Union[bool, None], str]
        if value is None:
            self._validation_result, self.validation_reason = None, "No reason"
            return self._validation_result, self._validation_reason
        if not isinstance(value, (int, float)):
            self._validation_result, self.validation_reason = False, "Value should be an integer, or float (floored)"
            return self._validation_result, self._validation_reason

        basereason = "Value '{}' should be a odd number".format(value)

        self._validation_result = int(value) % 2 > self.accuracy
        if self._validation_result:
            self._validation_reason = basereason.replace("should be", "is")
            return self._validation_result, self._validation_reason
        else:
            self._validation_reason = basereason
            return self._validation_result, self._validation_reason


class SingleReferenceValidator(PropertyValidator):
    """A single reference validator, ensuring that only a single reference is selected.

    .. versionadded:: 2.2
    """

    vtype = PropertyVTypes.SINGLEREFERENCE

    def _logic(self, value=None):
        # type: (Any) -> Tuple[Union[bool, None], str]
        if value is None:
            self._validation_result, self.validation_reason = None, "No reason"
            return self._validation_result, self._validation_reason
        if not isinstance(value, (list, tuple, set)):
            self._validation_result, self.validation_reason = False, "Value should be a list, tuple or set"
            return self._validation_result, self._validation_reason

        self._validation_result = len(value) == 1 or len(value) == 0
        if self._validation_result:
            self._validation_reason = "A single or no value is selected"
            return self._validation_result, self._validation_reason
        else:
            self._validation_reason = "More than a single instance is selected"
            return self._validation_result, self._validation_reason


class RegexStringValidator(PropertyValidator):
    """
    A regular expression string validator.

    With a configured regex pattern, a string value is compared and matched against this pattern. If there is
    a positive match, the validator validates correctly.

    For more information on constructing regex strings, see the `python documentation`_, `regex101.com`_, or
    `regexr.com`_.

    .. versionadded:: 2.2

    :ivar pattern: the regex pattern to which the provided value is matched against.

    Example
    -------
    >>> validator = RegexStringValidator(pattern=r"Yes|Y|1|Ok")
    >>> validator.is_valid("Yes")
    True
    >>> validator.is_valid("No")
    False

    .. _python documentation: https://docs.python.org/2/library/re.html
    .. _regex101.com: https://regex101.com/
    .. _regexr.com: https://regexr.com/
    """

    vtype = PropertyVTypes.REGEXSTRING

    def __init__(self, json=None, pattern=None, **kwargs):
        """Construct an regex string validator effect.

        If no pattern is provided than the regexstring `'.+'` will be used, which matches all provided text with
        at least a single character. Does not match `''` (empty string).

        :param json: (optional) dict (json) object to construct the object from
        :type json: dict
        :param pattern: (optional) valid regex string, defaults to r'.+' which matches all text.
        :type text: basestring
        :param kwargs: (optional) additional kwargs to pass down
        :type kwargs: dict
        """
        super(RegexStringValidator, self).__init__(json=json, **kwargs)

        if pattern is not None:
            self._config['pattern'] = pattern

        self.pattern = self._config.get('pattern', r'.+')
        self._re = re.compile(self.pattern)

    def _logic(self, value=None):
        # type: (Any) -> Tuple[Union[bool, None], str]
        if value is None:
            self._validation_result, self.validation_reason = None, "No reason"
            return self._validation_result, self._validation_reason

        basereason = "Value '{}' should match the regex pattern '{}'".format(value, self.pattern)

        self._validation_result = re.match(self._re, value) is not None
        if not self._validation_result:
            self._validation_reason = basereason
        else:
            self._validation_reason = basereason.replace('should match', 'matches')

        return self._validation_result, self._validation_reason
