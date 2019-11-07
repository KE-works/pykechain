from pykechain.enums import PropertyRepresentation
from pykechain.models.representations.representation_base import BaseRepresentation


class DecimalPlaces(BaseRepresentation):
    rtype = PropertyRepresentation.DECIMAL_PLACES


class SignificantDigits(BaseRepresentation):
    rtype = PropertyRepresentation.SIGNIFICANT_DIGITS


class LinkTarget(BaseRepresentation):
    rtype = PropertyRepresentation.LINK_TARGET


class ButtonRepresentation(BaseRepresentation):
    rtype = PropertyRepresentation.BUTTON
