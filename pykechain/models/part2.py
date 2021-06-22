from pykechain.exceptions import _DeprecationMixin
from pykechain.models import Part


class Part2(Part, _DeprecationMixin):
    """Deprecated Part2 class in favor of Part class."""

    pass
