from typing import Iterable, Any, Sized

from pykechain.models import Activity2
from pykechain.models.base_reference import _ReferenceProperty


class ActivityReferenceProperty(_ReferenceProperty):

    REFERENCED_CLASS = Activity2

    def _retrieve_objects(self, object_ids: Iterable[Any], **kwargs) -> Sized[Activity2]:
        return self._client.activities(id__in=','.join(object_ids))
