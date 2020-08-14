from pykechain.exceptions import _DeprecationMixin
from pykechain.models import Activity


class Activity2(Activity, _DeprecationMixin):
    """A virtual object representing a KE-chain activity.

    .. versionadded:: 2.0

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
    :ivar status: status of the activity. One of :class:`pykechain.enums.ActivityStatus`
    :type status: basestring
    :ivar classification: classification of the activity. One of :class:`pykechain.enums.ActivityClassification`
    :type classification: basestring
    :ivar activity_type: Type of the activity. One of :class:`pykechain.enums.ActivityType` for WIM version 2
    :type activity_type: basestring
    """

    pass
