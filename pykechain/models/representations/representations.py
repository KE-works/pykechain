from pykechain.enums import PropertyRepresentation, SelectListRepresentations, LinkTargets
from pykechain.exceptions import IllegalArgumentError
from pykechain.models.representations.representation_base import BaseRepresentation


class DecimalPlaces(BaseRepresentation):
    rtype = PropertyRepresentation.DECIMAL_PLACES
    _config_value_key = 'amount'

    def validate_representation(self, value):
        if not isinstance(value, int):
            raise IllegalArgumentError('{} value "{}" is not correct: not an integer'.format(
                self.__class__.__name__, value))


class SignificantDigits(DecimalPlaces):
    rtype = PropertyRepresentation.SIGNIFICANT_DIGITS


class LinkTarget(BaseRepresentation):
    rtype = PropertyRepresentation.LINK_TARGET
    _config_value_key = 'target'

    def validate_representation(self, value):
        if value not in LinkTargets.values():
            raise IllegalArgumentError('{} value "{}" is not correct: Not an CardWidgetLinkTarget option.'.format(
                self.__class__.__name__, value))


class ButtonRepresentation(BaseRepresentation):
    rtype = PropertyRepresentation.BUTTON
    _config_value_key = PropertyRepresentation.BUTTON

    def validate_representation(self, value):
        if value not in SelectListRepresentations.values():
            raise IllegalArgumentError('{} value "{}" is not correct: Not an SelectListRepresentations option.'.format(
                self.__class__.__name__, value))
