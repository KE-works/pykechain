from typing import List, Optional, Text

from pykechain.defaults import PARTS_BATCH_LIMIT
from pykechain.exceptions import IllegalArgumentError
from pykechain.models import Activity, Scope, user
from pykechain.models.base_reference import _ReferencePropertyInScope, _ReferenceProperty
from pykechain.models.value_filter import ScopeFilter
from pykechain.utils import get_in_chunks


class ActivityReferencesProperty(_ReferencePropertyInScope):
    """A virtual object representing a KE-chain Activity References property.

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


class ScopeReferencesProperty(_ReferenceProperty):
    """A virtual object representing a KE-chain Scope References property.

    .. versionadded: 3.9
    """

    REFERENCED_CLASS = Scope

    def _retrieve_objects(self, **kwargs) -> List[Scope]:
        """
        Retrieve a list of Scopes.

        :param kwargs: optional inputs
        :return: list of Scope2 objects
        """
        scope_ids = self._validate_values()

        scopes = []
        if scope_ids:
            scopes = list()
            for chunk in get_in_chunks(scope_ids, PARTS_BATCH_LIMIT):
                scopes.extend(list(self._client.scopes(id__in=",".join(chunk), status=None)))
        return scopes

    def set_prefilters(
            self,
            prefilters: List[ScopeFilter] = None,
            clear: Optional[bool] = False,
    ) -> None:
        """
        Set pre-filters on the scope reference property.

        :param prefilters: list of Scope Filter objects
        :type prefilters: list
        :param clear: whether all existing pre-filters should be cleared. (default = False)
        :type clear: bool

        :return: None
        """
        if prefilters is not None:
            if not isinstance(prefilters, list) or not all(isinstance(pf, ScopeFilter) for pf in prefilters):
                raise IllegalArgumentError(
                    "`prefilters` must be a list of ScopeFilter objects, `{}` is not.".format(prefilters))
        else:
            prefilters = []

        if not clear:
            list_of_prefilters = ScopeFilter.parse_options(options=self._options)
        else:
            list_of_prefilters = list()

        list_of_prefilters += prefilters

        # Only update the options if there are any prefilters to be set, or if the original filters have to overwritten
        if list_of_prefilters or clear:
            self._options.update(
                ScopeFilter.write_options(filters=list_of_prefilters)
            )
            self.edit(options=self._options)

    def get_prefilters(self) -> List[ScopeFilter]:
        """
        Return a list of ScopeFilter objects currently configured on the property.

        :return: list of ScopeFilter objects
        :rtype list
        """
        return ScopeFilter.parse_options(self._options)


class UserReferencesProperty(_ReferenceProperty):
    """A virtual object representing a KE-chain User References property.

    .. versionadded: 3.9
    """

    REFERENCED_CLASS = user.User

    def _validate_values(self) -> List[Text]:
        """
        Check if the `_value` attribute has valid content.

        :return list of UUIDs:
        :rtype list
        """
        if not self._value:
            return []

        object_ids = []
        for value in self._value:
            if isinstance(value, dict) and "pk" in value or "id" in value:
                pk = str(value.get("pk", value.get("id")))
                object_ids.append(pk)
            elif isinstance(value, (int, str)):
                object_ids.append(str(value))
            else:  # pragma: no cover
                raise ValueError(
                    'Value "{}" must be a dict with field `pk` or a UUID.'.format(value)
                )
        return object_ids

    def _retrieve_objects(self, **kwargs) -> List[user.User]:
        """
        Retrieve a list of Users.

        :param kwargs: optional inputs
        :return: list of User objects

        """
        user_ids = self._validate_values()

        users = []
        if user_ids:
            users = list()
            for chunk in get_in_chunks(user_ids, PARTS_BATCH_LIMIT):
                users.extend(list(self._client.users(id__in=",".join(chunk))))
        return users

    def value_ids(self) -> Optional[List[int]]:
        """
        Retrieve the referenced object UUIDs only.

        :return: list of UUIDs
        :rtype list
        """
        return [value.get("pk") for value in self._value] if self.has_value() else None
