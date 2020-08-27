from typing import List

from pykechain.models import Activity, Scope, user
from pykechain.models.base_reference import _ReferencePropertyInScope


class ActivityReferenceProperty(_ReferencePropertyInScope):
    """A virtual object representing a KE-chain Activity Reference property.

    .. versionadded:: 3.7
    """

    REFERENCED_CLASS = Activity

    def _retrieve_objects(self, **kwargs) -> List[Activity]:
        """
        Retrieve a list of Activities.

        :param kwargs: optional inputs
        :return: list of Activity2 objects
        """
        activities = []
        for activity_json in self._value:
            activity = Activity(client=self._client, json=activity_json)
            activity.refresh()  # To populate the object with all expected data
            activities.append(activity)
        return activities


class ScopeReferenceProperty(_ReferencePropertyInScope):
    """A virtual object representing a KE-chain Scope Reference property.

    .. versionadded: 3.9
    """

    REFERENCED_CLASS = Scope

    def _retrieve_objects(self, **kwargs) -> List[Scope]:
        """
        Retrieve a list of Scopes.

        :param kwargs: optional inputs
        :return: list of Scope2 objects
        """
        if not self._value:
            return []
        scope_ids = []
        for value in self._value:
            if isinstance(value, dict):
                scope_ids.append(value.get("id"))
            elif isinstance(value, str):
                scope_ids.append(value)
            else:
                raise ValueError(
                    'Value "{}" must be a dict with field `id` or a UUID.'.format(value)
                )

        scopes = []
        if scope_ids:
            scopes = list(self._client.scopes(id__in=",".join(scope_ids)))
        return scopes


class UserReferenceProperty(_ReferencePropertyInScope):
    """A virtual object representing a KE-chain User Reference property.

    .. versionadded: 3.9
    """

    REFERENCED_CLASS = user.User

    def _retrieve_objects(self, **kwargs) -> List[user.User]:
        """
        Retrieve a list of Users.

        :param kwargs: optional inputs
        :return: list of User objects

        """
        if not self._value:
            return []
        users_ids = []
        for value in self._value:
            if isinstance(value, dict) and "pk" in value:
                users_ids.append(str(value.get("pk")))
            elif isinstance(value, dict) and "id" in value:
                users_ids.append(str(value.get("id")))
            elif isinstance(value, str):
                users_ids.append(value)
            else:
                raise ValueError(
                    'Value "{}" must be a dict with field `pk` or a UUID.'.format(value)
                )

        users = []
        if users_ids:
            users = list(self._client.users(id__in=",".join(users_ids)))
        return users
