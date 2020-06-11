from pykechain.enums import (
    PropertyRepresentation,
    SelectListRepresentations,
    LinkTargets,
    FontAwesomeMode,
)
from pykechain.exceptions import IllegalArgumentError
from pykechain.models.input_checks import check_type
from pykechain.models.representations.representation_base import BaseRepresentation


class DecimalPlaces(BaseRepresentation):
    """Representation for floating-point value properties."""

    rtype = PropertyRepresentation.DECIMAL_PLACES
    _config_value_key = "amount"

    def validate_representation(self, value: int) -> None:
        """
        Validate whether the representation value can be set.

        :param value: representation value to set.
        :type value: int
        :return: None
        """
        if not isinstance(value, int):
            raise IllegalArgumentError(
                '{} value "{}" is not correct: not an integer'.format(
                    self.__class__.__name__, value
                )
            )


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
            raise IllegalArgumentError(
                '{} value "{}" is not correct: not NoneType'.format(
                    self.__class__.__name__, value
                )
            )


class LinkTarget(BaseRepresentation):
    """Representation for HTML link reference properties."""

    rtype = PropertyRepresentation.LINK_TARGET
    _config_value_key = "target"

    def validate_representation(self, value: LinkTargets) -> None:
        """
        Validate whether the representation value can be set.

        :param value: representation value to set.
        :type value: LinkTargets
        :return: None
        """
        if value not in LinkTargets.values():
            raise IllegalArgumentError(
                '{} value "{}" is not correct: Not a CardWidgetLinkTarget option.'.format(
                    self.__class__.__name__, value
                )
            )


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
            raise IllegalArgumentError(
                '{} value "{}" is not correct: Not a SelectListRepresentations option.'.format(
                    self.__class__.__name__, value
                )
            )


class Autofill(BaseRepresentation):
    """Representation for date(time) properties."""

    rtype = PropertyRepresentation.AUTOFILL
    _config_value_key = PropertyRepresentation.AUTOFILL

    def validate_representation(self, value: bool) -> None:
        """
        Validate whether the representation value can be set.

        :param value: representation value to set.
        :type value: bool
        :return: None
        """
        check_type(value, bool, "autofill")


class CustomIconRepresentation(BaseRepresentation):
    """Representation for scope and activities to display a custom Font Awesome icon."""

    rtype = "customIcon"
    _config_value_key = "displayIcon"
    _display_mode_key = "displayIconMode"

    def __init__(self, *args, **kwargs):
        """
        Create a custom icon representation.

        Display mode of the icon will be `regular` by default.
        """
        super().__init__(*args, **kwargs)
        if self._display_mode_key not in self._config:
            self._config[self._display_mode_key] = FontAwesomeMode.REGULAR

    def validate_representation(self, value: str):
        """
        Validate whether the representation value can be set.

        :param value: representation value to set.
        :type value: str
        :return: None
        """
        if not isinstance(value, str):
            raise IllegalArgumentError(
                '{} value "{}" is not correct: not a string'.format(
                    self.__class__.__name__, value
                )
            )

    @property
    def display_mode(self):
        """Get the the display mode of the custom icon representation."""
        return self._config[self._display_mode_key]

    @display_mode.setter
    def display_mode(self, mode: FontAwesomeMode) -> None:
        """
        Set the the display mode of the custom icon representation.

        :param mode: FontAwesome display mode
        :type mode: FontAwesomeMode
        """
        if mode not in set(FontAwesomeMode.values()):
            raise IllegalArgumentError(
                '{} mode "{}" is not a FontAwesomeMode option.'.format(
                    self.__class__.__name__, mode
                )
            )

        self._config[self._display_mode_key] = mode
        self.value = self.value  # trigger update
