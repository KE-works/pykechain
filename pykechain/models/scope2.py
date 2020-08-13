from pykechain.exceptions import _DeprecationMixin
from pykechain.models import Scope


class Scope2(Scope, _DeprecationMixin):
    """A virtual object representing a KE-chain scope.

    :ivar id: id of the activity
    :type id: uuid
    :ivar name: name of the activity
    :type name: basestring
    :ivar created_at: created datetime of the activity
    :type created_at: datetime
    :ivar updated_at: updated datetime of the activity
    :type updated_at: datetime
    :ivar description: description of the activity
    :type description: basestring
    :ivar workflow_root: uuid of the workflow root object
    :type workflow_root: uuid
    :ivar status: status of the scope. One of :class:`pykechain.enums.ScopeStatus`
    :type status: basestring
    :ivar type: Type of the Scope. One of :class:`pykechain.enums.ScopeType` for WIM version 2
    :type type: basestring
    """
    pass
