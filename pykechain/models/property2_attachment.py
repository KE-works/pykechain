from pykechain.exceptions import _DeprecationMixin
from pykechain.models import AttachmentProperty


class AttachmentProperty2(AttachmentProperty, _DeprecationMixin):
    """A virtual object representing a KE-chain attachment property."""

    pass
