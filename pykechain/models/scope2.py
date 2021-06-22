from pykechain.exceptions import _DeprecationMixin
from pykechain.models import Scope


class Scope2(Scope, _DeprecationMixin):
    """Deprecated Part2 class in favor of Part class."""

    pass
