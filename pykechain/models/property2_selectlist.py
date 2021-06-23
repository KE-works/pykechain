from pykechain.exceptions import _DeprecationMixin
from pykechain.models import MultiSelectListProperty, SelectListProperty


class SelectListProperty2(SelectListProperty, _DeprecationMixin):
    """A virtual object representing a KE-chain single-select list property."""

    pass


class MultiSelectListProperty2(MultiSelectListProperty, _DeprecationMixin):
    """A virtual object representing a KE-chain multi-select list property."""

    pass
