"""All pykechain surrogate models based on KE-chain models."""
from typing import Union

from .base import Base, BaseInScope
from .scope import Scope
from .scope2 import Scope2
from .activity import Activity
from .activity2 import Activity2
from .association import Association
from .part import Part
from .part2 import Part2
from .property import Property
from .property_attachment import AttachmentProperty
from .property_selectlist import SelectListProperty
from .property_multi_reference import MultiReferenceProperty
from .property_datetime import DatetimeProperty
from .property2 import Property2
from .property2_attachment import AttachmentProperty2
from .property2_selectlist import SelectListProperty2
from .property2_multi_reference import MultiReferenceProperty2
from .property2_datetime import DatetimeProperty2
from .property2_activity_reference import ActivityReferenceProperty
from .partset import PartSet
from .service import Service, ServiceExecution
from .team import Team
from .user import User
from ..enums import PropertyType

AnyProperty = Union[
    'Property',
    'MultiReferenceProperty',
    'AttachmentProperty',
    'SelectListProperty',
    'DatetimeProperty',
    'Property2',
    'MultiReferenceProperty2',
    'AttachmentProperty2',
    'SelectListProperty2',
    'DatetimeProperty2'
    'ActivityReferenceProperty',
]

# This map is used to identify the correct class for the (KE-chain provided) property type.
property_type_to_class_map = {
    PropertyType.ATTACHMENT_VALUE: AttachmentProperty2,
    PropertyType.SINGLE_SELECT_VALUE: SelectListProperty2,
    PropertyType.REFERENCES_VALUE: MultiReferenceProperty2,
    PropertyType.DATETIME_VALUE: DatetimeProperty2,
    PropertyType.ACTIVITY_REFERENCES_VALUE: ActivityReferenceProperty,
}

__all__ = (
    'Base',
    'BaseInScope',
    'Scope',
    'Scope2',
    'Activity',
    'Association',
    'Activity2',
    'Part',
    'Part2',
    'PartSet',
    'Service',
    'ServiceExecution',
    'User',
    'Team',
    'Property',
    'MultiReferenceProperty',
    'AttachmentProperty',
    'SelectListProperty',
    'DatetimeProperty',
    'Property2',
    'MultiReferenceProperty2',
    'AttachmentProperty2',
    'SelectListProperty2',
    'DatetimeProperty2',
    'ActivityReferenceProperty',
    'AnyProperty',
    'property_type_to_class_map',
)
