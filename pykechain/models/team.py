from typing import Optional, Union, List, Text, Dict

import requests

from pykechain.enums import TeamRoles, ScopeStatus
from pykechain.exceptions import APIError
from pykechain.models.user import User
from .base import Base
from .input_checks import check_text, check_type, check_enum, check_user


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
            raise APIError("Could not update Team {}".format(self), response=response)

        self.refresh(json=response.json().get('results')[0])

    def edit(
            self,
            name: Optional[Text] = None,
            description: Optional[Text] = None,
            options: Optional[Dict] = None,
            is_hidden: Optional[bool] = None
    ) -> None:
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
        update_dict = {
            'id': self.id,
            'name': check_text(name, 'name') or self.name,
            'description': check_text(description, 'description') or self.description,
            'options': check_type(options, dict, 'options') or self.options,
            'is_hidden': check_type(is_hidden, bool, 'is_hidden') or self.is_hidden,
        }

        self._update(resource='team', team_id=self.id, update_dict=update_dict)

    def delete(self) -> None:
        """
        Delete the team.

        Members of the team remain intact.

        :return: None
        """
        url = self._client._build_url(resource='team', team_id=self.id)
        response = self._client._request('DELETE', url=url)

        if response.status_code != requests.codes.no_content:  # pragma: no cover
            raise APIError("Could not delete Team {}".format(self), response=response)

    def members(self, role: Optional[Union[TeamRoles, Text]] = None) -> List[Dict]:
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
        check_enum(role, TeamRoles, 'role')

        member_list = list(self._json_data.get('members'))
        if role:
            return [teammember for teammember in member_list if teammember.get('role') == role]
        else:
            return member_list

    def add_members(self,
                    users: Optional[List[Union[User, Text]]] = None,
                    role: Optional[Union[TeamRoles, Text]] = TeamRoles.MEMBER,
                    ) -> None:
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
        update_dict = {
            'role': check_enum(role, TeamRoles, 'role'),
            'users': [check_user(user, User, 'users') for user in users],
        }

        self._update('team_add_members', team_id=self.id, update_dict=update_dict)

    def remove_members(self, users: Optional[List[Union[User, Text]]] = None) -> None:
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
        update_dict = {'users': [check_user(user, User, 'users') for user in users]}

        self._update('team_remove_members',
                     update_dict=update_dict,
                     team_id=self.id)

    def scopes(self, status: Optional[ScopeStatus] = None, **kwargs) -> List['Scope2']:
        """Scopes associated to the team."""
        return self._client.scopes(team=self.id, status=status, **kwargs)
