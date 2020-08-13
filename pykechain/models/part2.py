from pykechain.exceptions import _DeprecationMixin
from pykechain.models import Part


class Part2(Part, _DeprecationMixin):
    """A virtual object representing a KE-chain part.

    :ivar id: UUID of the part
    :type id: basestring
    :ivar name: Name of the part
    :type name: basestring
    :ivar ref: Reference of the part (slug of the original name)
    :type ref: basestring
    :ivar description: description of the part
    :type description: basestring or None
    :ivar created_at: the datetime when the object was created if available (otherwise None)
    :type created_at: datetime or None
    :ivar updated_at: the datetime when the object was last updated if available (otherwise None)
    :type updated_at: datetime or None
    :ivar category: The category of the part, either 'MODEL' or 'INSTANCE' (of :class:`pykechain.enums.Category`)
    :type category: basestring
    :ivar parent_id: The UUID of the parent of this part
    :type parent_id: basestring or None
    :ivar properties: The list of :class:`Property2` objects belonging to this part.
    :type properties: List[Property]
    :ivar multiplicity: The multiplicity of the part being one of the following options: ZERO_ONE, ONE, ZERO_MANY,
                        ONE_MANY, (reserved) M_N (of :class:`pykechain.enums.Multiplicity`)
    :type multiplicity: basestring
    :ivar scope_id: scope UUID of the Part
    :type scope_id: basestring
    :ivar properties: the list of properties of this part
    :type properties: List[AnyProperty]

    Examples
    --------
    For the category property

    >>> bike = project.part('Bike')
    >>> bike.category
    'INSTANCE'

    >>> bike_model = project.model('Bike')
    >>> bike_model.category
    'MODEL'

    >>> bike_model == Category.MODEL
    True
    >>> bike == Category.INSTANCE
    True

    For the multiplicity property

    >>> bike = project.models('Bike')
    >>> bike.multiplicity
    ONE_MANY

    >>> from pykechain.enums import Multiplicity
    >>> bike.multiplicity == Multiplicity.ONE_MANY
    True

    """
    pass
