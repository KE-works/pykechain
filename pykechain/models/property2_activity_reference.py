from typing import Iterable, Any

from pykechain.models import Activity2
from pykechain.models.base_reference import _ReferencePropertyInScope


class ActivityReferenceProperty(_ReferencePropertyInScope):
    """A virtual object representing a KE-chain Activity Reference property.

    .. versionadded:: 3.7
    """

    REFERENCED_CLASS = Activity2

    def _retrieve_objects(self, object_ids: Iterable[Any], **kwargs) -> Iterable[Activity2]:
        """
        Retrieve a list of Activities.

        :param object_ids: list of Activity UUIDs.
        :param kwargs: optional inputs
        :return: list of Activity2 objects
        """
        return self._client.activities(id__in=','.join(object_ids))
