from typing import List

from pykechain.models import Activity2
from pykechain.models.base_reference import _ReferencePropertyInScope


class ActivityReferenceProperty(_ReferencePropertyInScope):
    """A virtual object representing a KE-chain Activity Reference property.

    .. versionadded:: 3.7
    """

    REFERENCED_CLASS = Activity2

    def _retrieve_objects(self, **kwargs) -> List[Activity2]:
        """
        Retrieve a list of Activities.

        :param kwargs: optional inputs
        :return: list of Activity2 objects
        """
        activities = []
        for activity_json in self._value:
            activity = Activity2(client=self._client, json=activity_json)
            activity.refresh()  # To populate the object with all expected data
            activities.append(activity)
        return activities
