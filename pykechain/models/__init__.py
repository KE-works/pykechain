"""All pykechain surrogate models based on KE-chain models."""
from typing import Union

from .base import Base
from .scope2 import Scope2
from .activity2 import Activity2
from .association import Association
from .part2 import Part2
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
    'Scope2',
    'Association',
    'Activity2',
    'Part2',
    'PartSet',
    'Service',
    'ServiceExecution',
    'User',
    'Team',
    'Property2',
    'AnyProperty',
)
