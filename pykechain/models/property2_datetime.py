from pykechain.exceptions import _DeprecationMixin
from pykechain.models import DatetimeProperty


class DatetimeProperty2(DatetimeProperty, _DeprecationMixin):
    """A virtual object representing a KE-chain datetime property."""

    pass
