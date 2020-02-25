"""All pykechain surrogate models based on KE-chain models."""
from typing import Union

from .base import Base
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
from .property_reference import ReferenceProperty
from .property_multi_reference import MultiReferenceProperty
from .property2 import Property2
from .property2_attachment import AttachmentProperty2
from .property2_selectlist import SelectListProperty2
from .property2_multi_reference import MultiReferenceProperty2
from .property2_datetime import DatetimeProperty2
from .partset import PartSet
from .service import Service, ServiceExecution
from .team import Team
from .user import User

AnyProperty = Union[
    'Property2',
    'MultiReferenceProperty2',
    'AttachmentProperty2',
    'SelectListProperty2',
    'DatetimeProperty2'
]

__all__ = (
    'Base',
    'Scope',
    'Scope2',
    'Activity',
    'Association',
    'Activity2',
    'Part',
    'Part2',
    'PartSet',
    'Property',
    'AttachmentProperty',
    'SelectListProperty',
    'ReferenceProperty',
    'MultiReferenceProperty',
    'Property2',
    'AttachmentProperty2',
    'SelectListProperty2',
    'DatetimeProperty2',
    'MultiReferenceProperty2',
    'Service',
    'ServiceExecution',
    'User',
    'Team',
    'AnyProperty'
)
