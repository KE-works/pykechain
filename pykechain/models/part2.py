from typing import Any  # noqa: F401

from pykechain.enums import Multiplicity, Category
from pykechain.models import Part
from pykechain.models.property2 import Property2


class Part2(Part):
    """A virtual object representing a KE-chain part.

    :cvar basestring category: The category of the part, either 'MODEL' or 'INSTANCE'
                               (use :class:`pykechain.enums.Category`)
    :cvar basestring parent_id: The UUID of the parent of this part
    :cvar properties: The list of :class:`Property` objects belonging to this part.
    :cvar basestring multiplicity: The multiplicity of the part being one of the following options:
                                   ZERO_ONE, ONE, ZERO_MANY, ONE_MANY, (reserved) M_N

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

    def __init__(self, json, **kwargs):
        # type: (dict, **Any) -> None
        """Construct a part from a KE-chain 2 json response.

        :param json: the json response to construct the :class:`Part` from
        :type json: dict
        """
        super(Part, self).__init__(json, **kwargs)

        self.category = json.get('category')
        self.parent_id = json['parent'].get('id') if 'parent' in json and json.get('parent') else None
        self.multiplicity = json.get('multiplicity', None)
        self._cached_children = None

        self.properties = [Property2.create(p, client=self._client) for p in json['properties']]
