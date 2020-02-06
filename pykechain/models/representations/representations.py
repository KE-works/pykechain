from pykechain.enums import PropertyRepresentation, SelectListRepresentations, LinkTargets
from pykechain.exceptions import IllegalArgumentError
from pykechain.models.representations.representation_base import BaseRepresentation


class DecimalPlaces(BaseRepresentation):
    """Representation for floating-point value properties."""

    rtype = PropertyRepresentation.DECIMAL_PLACES
    _config_value_key = 'amount'

    def validate_representation(self, value):
        # type: (int) -> None
        """
        Validate whether the representation value can be set.

        :param value: representation value to set.
        :type value: int
        :return: None
        """
        if not isinstance(value, int):
            raise IllegalArgumentError('{} value "{}" is not correct: not an integer'.format(
                self.__class__.__name__, value))


class SignificantDigits(DecimalPlaces):
    """Representation for floating-point value properties."""

    rtype = PropertyRepresentation.SIGNIFICANT_DIGITS


class ThousandsSeparator(BaseRepresentation):
    """Representation for integer or floating-point value properties."""

    rtype = PropertyRepresentation.THOUSANDS_SEPARATOR

    def validate_representation(self, value):
        # type: (None) -> None
        """
        Validate whether the representation value can be set.

        :param value: representation value to set.
        :type value: int or float
        :return: None
        """
        if not (isinstance(value, type(None))):
            raise IllegalArgumentError('{} value "{}" is not correct: not NoneType'.format(
                self.__class__.__name__, value))


class LinkTarget(BaseRepresentation):
    """Representation for HTML link reference properties."""

    rtype = PropertyRepresentation.LINK_TARGET
    _config_value_key = 'target'

    def validate_representation(self, value):
        # type: (LinkTarget) -> None
        """
        Validate whether the representation value can be set.

        :param value: representation value to set.
        :type value: int
        :return: None
        """
        if value not in LinkTargets.values():
            raise IllegalArgumentError('{} value "{}" is not correct: Not an CardWidgetLinkTarget option.'.format(
                self.__class__.__name__, value))


class ButtonRepresentation(BaseRepresentation):
    """Representation for single-select list properties."""

    rtype = PropertyRepresentation.BUTTON
    _config_value_key = PropertyRepresentation.BUTTON

    def validate_representation(self, value):
        # type: (SelectListRepresentations) -> None
        """
        Validate whether the representation value can be set.

        :param value: representation value to set.
        :type value: int
        :return: None
        """
        if value not in SelectListRepresentations.values():
            raise IllegalArgumentError('{} value "{}" is not correct: Not an SelectListRepresentations option.'.format(
                self.__class__.__name__, value))
