from pykechain.exceptions import _DeprecationMixin
from pykechain.models import MultiReferenceProperty


class MultiReferenceProperty2(MultiReferenceProperty, _DeprecationMixin):
    """A virtual object representing a KE-chain multi-references property.

    .. versionadded:: 1.14
    """

    pass
