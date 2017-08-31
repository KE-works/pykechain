from typing import Any  # flake8: noqa

from pykechain.enums import Multiplicity
from pykechain.models.base import Base


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

    def add_members(self, members):
        """
        Add a single member, or multiple members (provided as list or tuple) to be added to the scope

        You may only edit the list of members if the pykechain credentials allow this.

        :param member: single username or list of usernames to be added to the scope list of members
        """
        select_action='add_member'

        if isinstance(members, str):
            pass
        elif isinstance(members, (list, tuple)):
            pass





