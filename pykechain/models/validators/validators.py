from __future__ import division

import mimetypes
import re
from typing import Any, Union, Tuple, Optional, Text, Dict, List  # noqa: F401 # pylint: disable=unused-import

from pykechain.enums import PropertyVTypes
from pykechain.models.validators.mime_types_defaults import predefined_mimes
from pykechain.models.validators.validator_schemas import filesizevalidator_schema, fileextensionvalidator_schema
from pykechain.models.validators.validators_base import PropertyValidator
from pykechain.utils import EMAIL_REGEX_PATTERN


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

        if self._config.get('minvalue') is None:
            self.minvalue = float('-inf')
        else:
            self.minvalue = self._config.get('minvalue')
        if self._config.get('maxvalue') is None:
            self.maxvalue = float('inf')
        else:
            self.maxvalue = self._config.get('maxvalue')

        self.stepsize = self._config.get('stepsize', None)
        self.enforce_stepsize = self._config.get('enforce_stepsize', None)

        if self.minvalue > self.maxvalue:
            raise Exception('The minvalue ({}) should be smaller than the maxvalue ({}) of the numeric '
                            'range validation'.format(self.minvalue, self.maxvalue))
        if self.enforce_stepsize and self.stepsize is None:
            raise Exception('The stepsize should be provided when enforcing stepsize')

    def _logic(self, value: Any = None) -> Tuple[Union[bool, None], str]:
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
                self._validation_result = abs(value / self.stepsize - round(value / self.stepsize)) < self.accuracy
            else:
                self._validation_result = abs((value - self.minvalue) / self.stepsize - round(
                    (value - self.minvalue) / self.stepsize)) < self.accuracy

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

    def _logic(self, value: Any = None) -> Tuple[Union[bool, None], str]:
        basereason = "Value is required"
        self._validation_result, self._validation_reason = None, "No reason"

        if value is not None and value != '' and value != list() and value != tuple() and value != set():
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

    def _logic(self, value: Any = None) -> Tuple[Union[bool, None], str]:
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

    def _logic(self, value: Any = None) -> Tuple[Union[bool, None], str]:
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

    def _logic(self, value: Any = None) -> Tuple[Union[bool, None], str]:
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
        """Construct an regex string validator.

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

    def _logic(self, value: Any = None) -> Tuple[Union[bool, None], str]:
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


class EmailValidator(RegexStringValidator):
    """
    A email string validator.

    :cvar pattern: the email regex pattern to which the provided value is matched against.
    """

    pattern = EMAIL_REGEX_PATTERN

    def __init__(self, json=None, **kwargs):
        """Construct an email string validator.

        :param json: (optional) dict (json) object to construct the object from
        :type json: dict
        :param kwargs: (optional) additional kwargs to pass down
        :type kwargs: dict
        """
        super(EmailValidator, self).__init__(json=json, pattern=self.pattern, **kwargs)


class AlwaysAllowValidator(PropertyValidator):
    """
    An always allow Validator.

    Will always return True.
    """

    vtype = PropertyVTypes.ALWAYSALLOW

    def _logic(self, value: Any = None) -> Tuple[Union[bool, None], str]:
        """Process the inner logic of the validator.

        The validation results are returned as tuple (boolean (true/false), reasontext)
        """
        return True, 'Always True'


class FileSizeValidator(PropertyValidator):
    """A file size Validator.

    The actual size of the file cannot be checked in pykechain without downloading this from the server, hence
    when the validator is used inside an attachment property, the validator returns always being valid.

    :ivar max_size: maximum size to check
    :type max_size: Union[int,float]

    Example
    -------
    >>> validator = FileSizeValidator(max_size=100)
    >>> validator.is_valid(100)
    True
    >>> validator.is_valid(-1)
    False
    >>> validator.is_valid("attachments/12345678-1234-5678-1234-567812345678/some_file.txt")
    True
    >>> validator.get_reason()
    We determine the filesize of 'some_file.txt' to be valid. We cannot check it at this end.

    """

    vtype = PropertyVTypes.FILESIZE
    jsonschema = filesizevalidator_schema

    def __init__(self, json: Optional[Dict] = None, max_size: Optional[Union[int, float]] = None, **kwargs):
        """Construct a file size validator.

        :param json: (optional) dict (json) object to construct the object from
        :type json: Optional[Dict]
        :param max_size: (optional) number that counts as maximum size of the file
        :type accept: Optional[Union[int,float]]
        :param kwargs: (optional) additional kwargs to pass down
        """
        super(FileSizeValidator, self).__init__(json=json, **kwargs)
        if max_size is not None:
            if isinstance(max_size, (int, float)):
                self._config['maxSize'] = int(max_size)
            else:
                raise ValueError("`max_size` should be a number.")
        self.max_size = self._config.get('maxSize', float('inf'))

    def _logic(self, value: Optional[Union[int, float]] = None) -> Tuple[Optional[bool], Optional[Text]]:
        """Based on a filesize (numeric) or  filepath of the property (value), the filesize is checked."""
        if value is None:
            return None, "No reason"

        basereason = "Value '{}' should be of a size less then '{}'".format(value, self.max_size)

        if isinstance(value, (int, float)):
            if int(value) <= self.max_size and int(value) >= 0:
                return True, basereason.replace("should", "is")
            else:
                return False, basereason

        return True, "We determine the filesize of '{}' to be valid. We cannot check it at this end.".format(value)


class FileExtensionValidator(PropertyValidator):
    """A file extension Validator.

    It checks the value of the property attachment against a list of acceptable mime types or file extensions.

    Example
    -------
    >>> validator = FileExtensionValidator(accept=[".png", ".jpg"])
    >>> validator.is_valid("picture.jpg")
    True
    >>> validator.is_valid("document.pdf")
    False
    >>> validator.is_valid("attachments/12345678-1234-5678-1234-567812345678/some_file.txt")
    False

    >>> validator = FileExtensionValidator(accept=["application/pdf",
    ...                                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"])
    >>> validator.is_valid("document.pdf")
    True
    >>> validator.is_valid("comma-separated-values.csv")
    False
    >>> validator.is_valid("attachments/12345678-1234-5678-1234-567812345678/modern_excel.xlsx")
    True

    """

    vtype = PropertyVTypes.FILEEXTENSION
    jsonschema = fileextensionvalidator_schema
    mimetype_regex = r'^[-\w.]+/[-\w.\*]+$'

    def __init__(self, json: Optional[Dict] = None, accept: Optional[Union[Text, List[Text]]] = None, **kwargs):
        """Construct a file extension validator.

        :param json: (optional) dict (json) object to construct the object from
        :type json: Optional[Dict]
        :param accept: (optional) list of mimetypes or file extensions (including a `.`, eg `.csv`, `.pdf`)
        :type accept: Optional[List[Text]]
        :param kwargs: (optional) additional kwargs to pass down
        """
        super(FileExtensionValidator, self).__init__(json=json, **kwargs)
        if accept is not None:
            if isinstance(accept, Text):
                self._config['accept'] = accept.split(',')
            elif isinstance(accept, List):
                self._config['accept'] = accept
            else:
                raise ValueError("`accept` should be a commaseparated list or a list of strings.")

        self.accept = self._config.get('accept', None)
        self._accepted_mimetypes = self._convert_to_mimetypes(self.accept)

    def _convert_to_mimetypes(self, accept: List[Text]) -> Optional[List[Text]]:
        """
        Convert accept array to array of mimetypes.

        1. convert accept list to array of mimetypes
        2. convert aggregator (if inside mime_types_defaults) to list of mimetypes

        :param accept: list of mimetypes or extensions
        :type accept: List[Text]
        :return: array of mimetypes:
        :rtype: List[Text]
        """
        if accept is None:
            return None

        marray = []
        for item in accept:
            # check if the item in the accept array is a mimetype on its own.
            if re.match(self.mimetype_regex, item):
                if item in predefined_mimes:
                    marray.extend(predefined_mimes.get(item))
                else:
                    marray.append(item)
            else:
                # we assume this is an extension.
                # we can only guess a url, we make a url like: "file.ext" to check.
                fake_filename = "file{}".format(item) if item.startswith(".") else "file.{}".format(item)

                # do guess
                guess, _ = mimetypes.guess_type(fake_filename)
                marray.append(guess) if guess is not None else print(guess)

        return marray

    def _logic(self, value: Optional[Text] = None) -> Tuple[Optional[bool], Optional[Text]]:
        """Based on the filename of the property (value), the type is checked.

        1. convert filename to mimetype
        3. check if the filename is inside the array of mimetypes. self._accepted_mimetypes
        """
        if value is None:
            return None, "No reason"

        basereason = "Value '{}' should match the mime types '{}'".format(value, self.accept)

        guessed_type, _ = mimetypes.guess_type(value)
        if guessed_type is None:
            return False, "Could not determine the mimetype of '{}'".format(value)
        elif guessed_type in self._accepted_mimetypes:
            return True, basereason.replace('match', 'matches')

        return False, basereason
