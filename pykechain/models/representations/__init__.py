"""All representations.

.. versionadded:: 3.0.x
"""
from .component import RepresentationsComponent
from .representation_base import BaseRepresentation
from .representations import (
    Autofill,
    ButtonRepresentation,
    CameraScannerInputRepresentation,
    CustomIconRepresentation,
    DecimalPlaces,
    GeoCoordinateRepresentation,
    LinkTarget,
    SignatureRepresentation,
    SignificantDigits,
    ThousandsSeparator,
    UsePropertyNameRepresentation,
)

AnyRepresentation = (
    BaseRepresentation,
    # Numbers
    DecimalPlaces,
    SignificantDigits,
    ThousandsSeparator,
    # Link properties
    LinkTarget,
    # Select lists
    ButtonRepresentation,
    # Date, Time, Datetime properties
    Autofill,
    # Scopes and activities
    CustomIconRepresentation,
    # Geocoordinate
    GeoCoordinateRepresentation,
    # Use Property Name for reference property
    UsePropertyNameRepresentation,
    # cameraScannerInput Representation for text inputs
    CameraScannerInputRepresentation,
    # Attachment properties
    SignatureRepresentation,
)

__all__ = (
    AnyRepresentation,
    RepresentationsComponent,
)

rtype_class_map = {r.rtype: r for r in AnyRepresentation}
