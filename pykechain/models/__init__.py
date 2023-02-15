"""All pykechain surrogate models based on KE-chain models."""
from typing import Union

# isort: off
from .base import Base, BaseInScope  # noqa

# isort: on
from ..enums import PropertyType
from .activity import Activity
from .activity2 import Activity2
from .association import Association
from .notification import Notification
from .part import Part
from .part2 import Part2
from .partset import PartSet
from .property import Property
from .property2 import Property2
from .property2_attachment import AttachmentProperty2
from .property2_datetime import DatetimeProperty2
from .property2_multi_reference import MultiReferenceProperty2
from .property2_selectlist import SelectListProperty2
from .property_attachment import AttachmentProperty
from .property_datetime import DatetimeProperty
from .property_multi_reference import MultiReferenceProperty
from .property_reference import (
    ActivityReferencesProperty,
    ContextReferencesProperty,
    FormReferencesProperty,
    ScopeReferencesProperty,
    StatusReferencesProperty,
    UserReferencesProperty,
)
from .property_selectlist import MultiSelectListProperty, SelectListProperty
from .scope import Scope
from .scope2 import Scope2
from .service import Service, ServiceExecution
from .team import Team
from .user import User
from .value_filter import PropertyValueFilter

AnyProperty = Union[
    "Property",
    "MultiReferenceProperty",
    "AttachmentProperty",
    "SelectListProperty",
    "DatetimeProperty",
    "Property2",
    "MultiReferenceProperty2",
    "AttachmentProperty2",
    "SelectListProperty2",
    "DatetimeProperty2",
    "ActivityReferencesProperty",
    "ScopeReferencesProperty",
    "UserReferencesProperty",
    "FormReferencesProperty",
    "ContextReferencesProperty",
    "StatusReferencesProperty",
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
    PropertyType.FORM_REFERENCES_VALUE: FormReferencesProperty,
    PropertyType.CONTEXT_REFERENCES_VALUE: ContextReferencesProperty,
    PropertyType.STATUS_REFERENCES_VALUE: StatusReferencesProperty,
}

__all__ = (
    "Base",
    "BaseInScope",
    "Scope",
    "Scope2",
    "Activity",
    "Association",
    "Activity2",
    "Part",
    "Part2",
    "PartSet",
    "Service",
    "ServiceExecution",
    "User",
    "Team",
    "Property",
    "MultiReferenceProperty",
    "AttachmentProperty",
    "SelectListProperty",
    "DatetimeProperty",
    "Property2",
    "MultiReferenceProperty2",
    "AttachmentProperty2",
    "SelectListProperty2",
    "DatetimeProperty2",
    "ActivityReferencesProperty",
    "ScopeReferencesProperty",
    "UserReferencesProperty",
    "FormReferencesProperty",
    "StatusReferencesProperty",
    "AnyProperty",
    "PropertyValueFilter",
    "Notification",
    "property_type_to_class_map",
)
