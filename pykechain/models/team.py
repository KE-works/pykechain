from typing import Optional, Union, List, Text, Dict, Any

import requests

from pykechain.enums import TeamRoles, ScopeStatus
from pykechain.exceptions import IllegalArgumentError, APIError
from pykechain.models.user import User
from .base import Base


class Team(Base):
    """A virtual object representing a KE-chain Team.

    :ivar name: team name
    :ivar id: uuid of the team
    """

    def __init__(self, json, **kwargs):
        """Construct a team from provided json data."""
        super(Team, self).__init__(json, **kwargs)

        self.ref = json.get('ref')
        self.description = json.get('description')
        self.options = json.get('options')
        self.is_hidden = json.get('is_hidden')

    def _update(self, resource, update_dict=None, params=None, **kwargs):
        """Update the team in-place."""
        url = self._client._build_url(resource, **kwargs)
        response = self._client._request('PUT', url, json=update_dict, params=params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update {} ({})".format(self.__class__.__name__, response.json().get('results')))

        self.refresh(json=response.json().get('results')[0])

    def edit(self, name=None, description=None, options=None, is_hidden=None):
        # type: (Text, Text, Dict, bool) -> None
        """
        Edit the attributes of the Team.

        :param name: (o) name of the Team
        :type name: str
        :param description: (o) description of the Team
        :type description: str
        :param options: (o) options dictionary to set attributes such as `landingPage`.
        :type options: dict
        :param is_hidden: flag to hide the Team
        :type is_hidden: bool
        :return: None
        :raises IllegalArgumentError whenever inputs are not of the correct type
        """
        update_dict = dict(id=self.id)
        if name is not None:
            if not isinstance(name, str):
                raise IllegalArgumentError('`name` must be a string, "{}" is not.'.format(name))
            update_dict.update({'name': name})

        if description is not None:
            if not isinstance(description, str):
                raise IllegalArgumentError('`description` must be a string, "{}" is not.'.format(description))
            update_dict.update({'description': description})

        if options is not None:
            if not isinstance(options, dict):
                raise IllegalArgumentError('`options` must be a dictionary, "{}" is not.'.format(options))
            update_dict.update({'options': options})

        if is_hidden is not None:
            if not isinstance(is_hidden, bool):
                raise IllegalArgumentError('`is_hidden` must be a boolean, "{}" is not.'.format(is_hidden))
            update_dict.update({'is_hidden': is_hidden})

        self._update(resource='team', team_id=self.id, update_dict=update_dict)

    def delete(self):
        # type: () -> None
        """
        Delete the team.

        Members of the team remain intact.

        :return: None
        """
        url = self._client._build_url(resource='team', team_id=self.id)
        response = self._client._request('DELETE', url=url)

        if response.status_code != requests.codes.no_content:  # pragma: no cover
            raise APIError("Could not delete team: {} with id {}".format(self.name, self.id))

    def members(self, role=None):
        # type: (Optional[Union[TeamRoles, Text]]) -> List[Dict]
        """Members of the team.

        You may provide the role in the team, to retrieve only the team member with that role. Normally there is a
        single owner, that has administration rights of the team. Normal team members do not have any rights to
        administer the team itself such as altering the team name, team image and team members. Administrators do
        have the right to administer the the team members.

        :param role: (optional) member belonging to a role :class:`pykechain.enums.TeamRoles` to return.
        :type role: basestring or None
        :raises IllegalArgumentError: when providing incorrect roles
        :return: list of dictionaries with members (pk, username, role, email)

        Example
        -------
        >>> my_team = client.team(name='My own team')
        >>> my_team.members()
        [{"pk":1, "username"="first user", "role"="OWNER", "email":"email@address.com"}, ...]

        """
        if role and role not in TeamRoles.values():
            raise IllegalArgumentError("role should be one of `TeamRoles` {}, got '{}'".format(TeamRoles.values(),
                                                                                               role))

        member_list = self._json_data.get('members')
        if role:
            return [teammember for teammember in member_list if teammember.get('role') == role]
        else:
            return member_list

    def add_members(self, users=None, role=TeamRoles.MEMBER):
        # type: (Optional[List[Union[User, Text]]], Optional[Union[TeamRoles, Text]]) -> ()
        """Members to add to a team.

        :param users: list of members, either `User` objects or usernames
        :type users: List of `User` or List of pk
        :param role: (optional) role of the users to add (default `TeamRoles.MEMBER`)
        :type role: basestring
        :raises IllegalArgumentError: when providing incorrect user information

        Example
        -------
        >>> my_team = client.team(name='My own team')
        >>> other_user = client.users(name='That other person')
        >>> myself = client.users(name='myself')
        >>> my_team.add_members([myself], role=TeamRoles.MANAGER)
        >>> my_team.add_members([other_user], role=TeamRoles.MEMBER)

        """
        if role and role not in TeamRoles.values():
            raise IllegalArgumentError("role should be one of `TeamRoles` {}, got '{}'".format(TeamRoles.values(),
                                                                                               role))

        if not users or not isinstance(users, (list, tuple, set)):
            raise IllegalArgumentError("users should be a list of user_ids or `User` objects, got '{}'".
                                       format(users))

        update_dict = dict(role=role)

        if all(isinstance(user, int) for user in users):
            update_dict['users'] = users
        elif all(isinstance(user, User) for user in users):
            update_dict['users'] = [user.id for user in users]
        else:
            raise IllegalArgumentError("All users should be a list of user_ids or `User` objects, got '{}'".
                                       format(users))

        self._update('team_add_members', team_id=self.id, update_dict=update_dict)

    def remove_members(self, users=None):
        # type: (Optional[List[Union[User, Text]]]) -> ()
        """
        Remove members from the team.

        :param users: list of members, either `User` objects or usernames
        :type users: List of `User` or List of pk
        :raises IllegalArgumentError: when providing incorrect user information


        Example
        -------
        >>> my_team = client.team(name='My own team')
        >>> other_user = client.users(name='That other person')
        >>> my_team.remove_members([other_user])

        """
        if not users or not isinstance(users, (list, tuple, set)):
            raise IllegalArgumentError("Member should be a list of user_ids or `User` objects, got '{}'".
                                       format(users))

        update_dict = dict()

        if all(isinstance(user, int) for user in users):
            update_dict['users'] = users
        elif all(isinstance(user, User) for user in users):
            update_dict['users'] = [user.id for user in users]
        else:
            raise IllegalArgumentError("All users should be a list of user_ids or `User` objects, got '{}'".
                                       format(users))

        self._update('team_remove_members',
                     update_dict=update_dict,
                     team_id=self.id)

    def scopes(self, status=None, **kwargs):
        # type: (ScopeStatus, **Any) -> List[Scope2]
        """Scopes associated to the team."""
        return self._client.scopes(team=self.id, status=status, **kwargs)
