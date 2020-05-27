"""All representations.

.. versionadded:: 3.0.x
"""
from .representation_base import BaseRepresentation
from .representations import (
    DecimalPlaces, SignificantDigits, ThousandsSeparator, LinkTarget, ButtonRepresentation, CustomIconRepresentation,
)

rtype_class_map = {
    DecimalPlaces.rtype: DecimalPlaces,
    SignificantDigits.rtype: SignificantDigits,
    ThousandsSeparator.rtype: ThousandsSeparator,
    LinkTarget.rtype: LinkTarget,
    ButtonRepresentation.rtype: ButtonRepresentation,
    CustomIconRepresentation.rtype: CustomIconRepresentation,
}

__all__ = [
    BaseRepresentation,

    # Numbers
    DecimalPlaces,
    SignificantDigits,
    ThousandsSeparator,

    # Link properties
    LinkTarget,

    # Select lists
    ButtonRepresentation,

    # Scopes and activities
    CustomIconRepresentation,
]
