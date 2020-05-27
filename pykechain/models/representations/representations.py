from pykechain.enums import PropertyRepresentation, SelectListRepresentations, LinkTargets, FontAwesomeMode
from pykechain.exceptions import IllegalArgumentError
from pykechain.models.representations.representation_base import BaseRepresentation


class DecimalPlaces(BaseRepresentation):
    """Representation for floating-point value properties."""

    rtype = PropertyRepresentation.DECIMAL_PLACES
    _config_value_key = 'amount'

    def validate_representation(self, value: int) -> None:
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

    def validate_representation(self, value: LinkTargets) -> None:
        """
        Validate whether the representation value can be set.

        :param value: representation value to set.
        :type value: LinkTargets
        :return: None
        """
        if value not in LinkTargets.values():
            raise IllegalArgumentError('{} value "{}" is not correct: Not a CardWidgetLinkTarget option.'.format(
                self.__class__.__name__, value))


class ButtonRepresentation(BaseRepresentation):
    """Representation for single-select list properties."""

    rtype = PropertyRepresentation.BUTTON
    _config_value_key = PropertyRepresentation.BUTTON

    def validate_representation(self, value: SelectListRepresentations) -> None:
        """
        Validate whether the representation value can be set.

        :param value: representation value to set.
        :type value: SelectListRepresentations
        :return: None
        """
        if value not in SelectListRepresentations.values():
            raise IllegalArgumentError('{} value "{}" is not correct: Not a SelectListRepresentations option.'.format(
                self.__class__.__name__, value))


class CustomIconRepresentation(BaseRepresentation):
    """Representation for scope and activities to display a custom Font Awesome icon."""

    rtype = 'customIcon'
    _config_value_key = 'displayIcon'

    def validate_representation(self, value: str):
        """
        Validate whether the representation value can be set.

        :param value: representation value to set.
        :type value: str
        :return: None
        """
        if value is None:
            raise IllegalArgumentError('{} value "{}" is not correct: not a string'.format(
                self.__class__.__name__, value))

    def set_display_mode(self, mode: FontAwesomeMode) -> None:
        """
        Change the display mode of the custom icon representation.

        :param mode: FontAwesome display mode
        :type mode: FontAwesomeMode
        """
        if mode not in set(FontAwesomeMode.values()):
            raise IllegalArgumentError('{} mode "{}" is not a FontAwesomeMode option.'.format(
                self.__class__.__name__, mode))

        current_value = self._value
        current_value['displayIconMode'] = mode
        self.value = current_value
