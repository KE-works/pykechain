from pykechain.exceptions import _DeprecationMixin
from pykechain.models import Activity


class Activity2(Activity, _DeprecationMixin):
    """A virtual object representing a KE-chain activity.

    .. versionadded:: 2.0

    :ivar id: id of the activity
    :ivar name: name of the activity
    :ivar created_at: created datetime of the activity
    :ivar updated_at: updated datetime of the activity
    :ivar description: description of the activity
    :ivar status: status of the activity. One of :class:`pykechain.enums.ActivityStatus`
    :ivar classification: classification of the activity. One of :class:`pykechain.enums.ActivityClassification`
    :ivar activity_type: Type of the activity. One of :class:`pykechain.enums.ActivityType` for WIM version 2
    """

    pass
