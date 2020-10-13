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
from .property_selectlist import SelectListProperty, MultiSelectListProperty
from .property_multi_reference import MultiReferenceProperty
from .property_datetime import DatetimeProperty
from .property2 import Property2
from .property2_attachment import AttachmentProperty2
from .property2_selectlist import SelectListProperty2
from .property2_multi_reference import MultiReferenceProperty2
from .property2_datetime import DatetimeProperty2
from .property_reference import ActivityReferencesProperty, ScopeReferencesProperty, UserReferencesProperty
from .partset import PartSet
from .service import Service, ServiceExecution
from .team import Team
from .user import User
from .value_filter import PropertyValueFilter
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
    'ActivityReferencesProperty',
    'ScopeReferencesProperty',
    'UserReferencesProperty',
]

# This map is used to identify the correct class for the (KE-chain provided) property type.
property_type_to_class_map = {
    PropertyType.ATTACHMENT_VALUE: AttachmentProperty,
    PropertyType.SINGLE_SELECT_VALUE: SelectListProperty,
    PropertyType.MULTI_SELECT_VALUE: MultiSelectListProperty,
    PropertyType.REFERENCES_VALUE: MultiReferenceProperty,
    PropertyType.DATETIME_VALUE: DatetimeProperty,
    PropertyType.ACTIVITY_REFERENCES_VALUE: ActivityReferencesProperty,
    PropertyType.SCOPE_REFERENCES_VALUE: ScopeReferencesProperty,
    PropertyType.USER_REFERENCES_VALUE: UserReferencesProperty,
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
    'ActivityReferencesProperty',
    'ScopeReferencesProperty',
    'UserReferencesProperty',
    'AnyProperty',
    'PropertyValueFilter',
    'property_type_to_class_map',
)
