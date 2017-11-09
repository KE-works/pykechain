from typing import Any  # flake8: noqa
import requests

from pykechain.enums import Multiplicity
from pykechain.models.base import Base
from pykechain.exceptions import APIError, NotFoundError


class Scope(Base):
    """A virtual object representing a KE-chain scope."""

    def __init__(self, json, **kwargs):
        # type: (dict, **Any) -> None
        """Construct a scope from provided json data."""
        super(Scope, self).__init__(json, **kwargs)

        self.bucket = json.get('bucket', {})
        self.process = json.get('process')

    def __repr__(self):  # pragma: no cover
        return "<pyke Scope '{}' id {}>".format(self.name, self.id[-8:])

    def parts(self, *args, **kwargs):
        """Retrieve parts belonging to this scope.

        See :class:`pykechain.Client.parts` for available parameters.
        """
        return self._client.parts(*args, bucket=self.bucket.get('id'), **kwargs)

    def part(self, *args, **kwargs):
        """Retrieve a single part belonging to this scope.

        See :class:`pykechain.Client.part` for available parameters.
        """
        return self._client.part(*args, bucket=self.bucket.get('id'), **kwargs)

    def create_model(self, parent, name, multiplicity=Multiplicity.ZERO_MANY):
        """Create a single part model in this scope.

        See :class:`pykechain.Client.create_model` for available parameters.
        """
        return self._client.create_model(parent, name, multiplicity=multiplicity)

    def model(self, *args, **kwargs):
        """Retrieve a single model belonging to this scope.

        See :class:`pykechain.Client.model` for available parameters.
        """
        return self._client.model(*args, bucket=self.bucket.get('id'), **kwargs)

    def activities(self, *args, **kwargs):
        """Retrieve activities belonging to this scope.

        See :class:`pykechain.Client.activities` for available parameters.
        """
        return self._client.activities(*args, scope=self.id, **kwargs)

    def activity(self, *args, **kwargs):
        """Retrieve a single activity belonging to this scope.

        See :class:`pykechain.Client.activity` for available parameters.
        """
        return self._client.activity(*args, scope=self.id, **kwargs)

    def create_activity(self, *args, **kwargs):
        """Create a new activity belonging to this scope.

        See :class:`pykechain.Client.create_activity` for available parameters.
        """
        return self._client.create_activity(self.process, *args, **kwargs)

    def services(self, *args, **kwargs):
        """Retrieve services belonging to this scope.

        See :class:`pykechain.Client.services` for available parameters.

        .. versionadded:: 1.13
        """
        return self._client.services(*args, scope=self.id, **kwargs)

    def create_service(self, *args, **kwargs):
        """Create a service to current scope.

        See :class:`pykechain.Client.create_service` for available parameters.

        .. versionadded:: 1.13
        """
        return self._client.create_service(*args, scope=self.id, **kwargs)

    def service(self, *args, **kwargs):
        """Retrieve a single service belonging to this scope.

        See :class:`pykechain.Client.service` for available parameters.

        .. versionadded:: 1.13
        """
        return self._client.service(*args, scope=self.id, **kwargs)

    def service_executions(self, *args, **kwargs):
        """Retrieve services belonging to this scope.

        See :class:`pykechain.Client.service_executions` for available parameters.

        .. versionadded:: 1.13
        """
        return self._client.service_executions(*args, scope=self.id, **kwargs)

    def service_execution(self, *args, **kwargs):
        """Retrieve a single service execution belonging to this scope.

        See :class:`pykechain.Client.service_execution` for available parameters.

        .. versionadded:: 1.13
        """
        return self._client.service_execution(*args, scope=self.id, **kwargs)

    def members(self, is_manager=None):
        """
        Retrieve members of the scope.

        :param is_manager: (optional) set to True to return only Scope members that are also managers.
        :return: List of members (usernames)

        Examples
        --------
        >>> members = project.members()
        >>> managers = project.members(is_manager=True)

        """
        if not is_manager:
            return [member for member in self._json_data['members'] if member['is_active']]
        else:
            return [member for member in self._json_data['members'] if
                    member.get('is_active', False) and member.get('is_manager', False)]

    def add_member(self, member):
        """
        Add a single member to the scope.

        You may only edit the list of members if the pykechain credentials allow this.

        :param member: single username to be added to the scope list of members
        """
        select_action = 'add_member'

        self._update_scope_project_team(select_action=select_action, user=member, user_type='member')

    def remove_member(self, member):
        """
        Remove a single member to the scope.

        :param member: single username to be removed to the scope list of members
        """
        select_action = 'remove_member'

        self._update_scope_project_team(select_action=select_action, user=member, user_type='member')

    def add_manager(self, manager):
        """
        Add a single manager to the scope.

        :param manager: single username to be added to the scope list of managers
        """
        select_action = 'add_manager'

        self._update_scope_project_team(select_action=select_action, user=manager, user_type='manager')

    def remove_manager(self, manager):
        """
        Remove a single manager to the scope.

        :param manager: single username to be removed to the scope list of managers
        """
        select_action = 'remove_manager'

        self._update_scope_project_team(select_action=select_action, user=manager, user_type='manager')

    def _update_scope_project_team(self, select_action, user, user_type):
        """
        Update the Project Team of the Scope. Updates include addition or removing of managers or members.

        :param select_action: type of action to be applied
        :param user: the username of the user to which the action applies to
        :param user_type: the type of the user (member or manager)
        """
        if isinstance(user, str):
            users = self._client._retrieve_users()
            manager_object = next((item for item in users['results'] if item["username"] == user), None)
            if manager_object:
                url = self._client._build_url('scope', scope_id=self.id)
                r = self._client._request('PUT', url, params={'select_action': select_action},
                                          data={
                                              'user_id': manager_object['pk']
                                          })
                if r.status_code != requests.codes.ok:  # pragma: no cover
                    raise APIError("Could not {} {} in Scope".format(select_action.split('_')[0], user_type))
            else:
                raise NotFoundError("User {} does not exist".format(user))
        else:
            raise TypeError("User {} should be defined as a string".format(user))

