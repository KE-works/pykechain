import requests

from pykechain.enums import TeamRoles
from pykechain.exceptions import IllegalArgumentError, APIError
from .base import Base


class Team(Base):
    """A virtual object representing a KE-chain Team.

    :ivar name: team name
    :ivar id: teamid of the user
    """

    def __init__(self, json, **kwargs):
        """Construct a user from provided json data."""
        super(Team, self).__init__(json, **kwargs)

        self.name = self._json_data.get('name', '')
        self.id = self._json_data.get('id', '')

    def __repr__(self):  # pragma: no cover
        return "<pyke {} '{}' id {}>".format(self.__class__.__name__, self.name, self.id)

    def _update(self, resource, update_dict=None, params=None, **kwargs):
        """Update the object."""
        url = self._client._build_url(resource, **kwargs)
        response = self._client._request('PUT', url, json=update_dict, params=params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update {} ({})".format(self.__class__.__name__, response.json().get('results')))
        else:
            self.refresh()

    def members(self, role=None):
        """Members of the team.

        You may provide the role in the team, to retrieve only the teammmber with that role. Normally there is a
        single owner, that has administration rights of the team. Normal team members do not have any rights to
        administer the team itself such as altering the teamname, team image and team members. Administrators do
        have the right to administer the the team members.

        :param role: (optional) member belonging to a role :class:`pykechain.enums.TeamRoles` to return.
        :type role: basestring or None
        :raises IllegalArgumentError: when providing incorrect roles
        :return: list of dictionaries with members (pk, username, role, email)
        """
        if role and role not in TeamRoles.values():
            raise IllegalArgumentError("role should be one of `TeamRoles` {}, got '{}'".format(TeamRoles.values(),
                                                                                               role))

        member_list = self._json_data.get('members')
        if role:
            return [teammember for teammember in member_list if teammember.get('role') == role]
        else:
            return member_list

    def add_members(self, members=None, role=TeamRoles.MEMBER):
        """Members to add to a team.

        :param members: list of members, either `User` objects or usernames
        :type members: List of `User` or List of pk
        :param role: (optional) role of the users to add (default `TeamRoles.MEMBER`)
        :type role: basestring
        :raises IllegalArgumentError: when providing incorrect roles
        """
        if role and role not in TeamRoles.values():
            raise IllegalArgumentError("role should be one of `TeamRoles` {}, got '{}'".format(TeamRoles.values(),
                                                                                               role))

        if not members or not isinstance(members, (list, tuple, set)):
            raise IllegalArgumentError("Member should be a list of user_ids or `User` objects, got '{}'".
                                       format(members))

        update_dict = dict(role=role)

        if all(isinstance(member, int) for member in members):
            update_dict['users'] = members

        self._update('team_add_members',
                     team_id=self.id,
                     update_dict=update_dict)

    def remove_members(self, members=None):
        """Members to add to a team.

        :param members: list of members, either `User` objects or usernames
        :type members: List of `User` or List of pk
        :raises IllegalArgumentError: when providing incorrect roles
        """
        if not members or not isinstance(members, (list, tuple, set)):
            raise IllegalArgumentError("Member should be a list of user_ids or `User` objects, got '{}'".
                                       format(members))

        update_dict = dict()

        if all(isinstance(member, int) for member in members):
            update_dict['users'] = members

        self._update('team_remove_members',
                     update_dict=update_dict,
                     team_id=self.id)

    def scopes(self, **kwargs):
        """Scopes associated to the team."""
        return self._client.scopes(team=self.id, **kwargs)
