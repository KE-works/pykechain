import datetime
import warnings
from typing import Any  # flake8: noqa

import requests
from six import text_type

from pykechain.enums import Multiplicity, ScopeStatus
from pykechain.exceptions import APIError, NotFoundError, IllegalArgumentError
from pykechain.models.base import Base
from pykechain.utils import is_uuid


class Scope(Base):
    """A virtual object representing a KE-chain scope."""

    def __init__(self, json, **kwargs):
        # type: (dict, **Any) -> None
        """Construct a scope from provided json data."""
        super(Scope, self).__init__(json, **kwargs)

        self.bucket = json.get('bucket', {})

        # for 'kechain2.core.wim <2.0.0'
        self.process = json.get('process')
        # for 'kechain2.core.wim >=2.0.0'
        self.workflow_root = json.get('workflow_root_id')

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
        if self._client.match_app_version(label='wim', version='<2.0.0', default=True):
            return self._client.activities(*args, scope=self.id, **kwargs)
        else:
            return self._client.activities(*args, scope_id=self.id, **kwargs)

    def activity(self, *args, **kwargs):
        """Retrieve a single activity belonging to this scope.

        See :class:`pykechain.Client.activity` for available parameters.
        """
        if self._client.match_app_version(label='wim', version='<2.0.0', default=True):
            return self._client.activity(*args, scope=self.id, **kwargs)
        else:
            return self._client.activity(*args, scope_id=self.id, **kwargs)

    def create_activity(self, *args, **kwargs):
        """Create a new activity belonging to this scope.

        See :class:`pykechain.Client.create_activity` for available parameters.
        """
        if self._client.match_app_version(label='wim', version='<2.0.0', default=True):
            return self._client.create_activity(self.process, *args, **kwargs)
        else:
            return self._client.create_activity(self.workflow_root, *args, **kwargs)

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
        :type is_manager: bool
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
        :type member: basestring
        :raises APIError: when unable to update the scope member
        """
        select_action = 'add_member'

        self._update_scope_project_team(select_action=select_action, user=member, user_type='member')

    def remove_member(self, member):
        """
        Remove a single member to the scope.

        :param member: single username to be removed from the scope list of members
        :type member: basestring
        :raises APIError: when unable to update the scope member
        """
        select_action = 'remove_member'

        self._update_scope_project_team(select_action=select_action, user=member, user_type='member')

    def add_manager(self, manager):
        """
        Add a single manager to the scope.

        :param manager: single username to be added to the scope list of managers
        :type manager: basestring
        :raises APIError: when unable to update the scope manager
        """
        select_action = 'add_manager'

        self._update_scope_project_team(select_action=select_action, user=manager, user_type='manager')

    def remove_manager(self, manager):
        """
        Remove a single manager to the scope.

        :param manager: single username to be added to the scope list of managers
        :type manager: basestring
        :raises APIError: when unable to update the scope manager
        """
        select_action = 'remove_manager'

        self._update_scope_project_team(select_action=select_action, user=manager, user_type='manager')

    def _update_scope_project_team(self, select_action, user, user_type):
        """
        Update the Project Team of the Scope. Updates include addition or removing of managers or members.

        :param select_action: type of action to be applied
        :type select_action: basestring
        :param user: the username of the user to which the action applies to
        :type user: basestring
        :param user_type: the type of the user (member or manager)
        :type user_type: basestring
        :raises APIError: When unable to update the scope project team.
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

    def edit(self, name=None, description=None, start_date=None, due_date=None, status=None, tags=None, team=None,
             options=None, **kwargs):
        """Edit the details of a scope.

        :param name: (optionally) edit the name of the scope
        :type name: basestring or None
        :param description: (optionally) edit the description of the scope
        :type description: basestring or None
        :param start_date: (optionally) edit the start date of the scope as a datetime object (UTC time/timezone
                            aware preferred)
        :type start_date: datetime or None
        :param due_date: (optionally) edit the due_date of the scope as a datetime object (UTC time/timzeone
                            aware preferred)
        :type due_date: datetime or None
        :param status: (optionally) edit the status of the scope as a string based
        :type status: basestring or None
        :param tags: (optionally) replace the tags on a scope, which is a list of strings ["one","two","three"]
        :type tags: list of basestring or None
        :param team: (optionally) add the scope to a team
        :type team: UUIDstring or None
        :param options: (optionally) custom options dictionary stored on the scope object
        :type options: dict or None
        :raises IllegalArgumentError: if the type of the inputs is not correct
        :raises APIError: if another Error occurs
        :warns: UserWarning - When a naive datetime is provided. Defaults to UTC.

        Example
        -------
        >>> from datetime import datetime
        >>> project.edit(name='New project name',
        ...              description='Changing the description just because I can',
        ...              start_date=datetime.utcnow(),  # naive time is interpreted as UTC time
        ...              status=ScopeStatus.CLOSED)

        If we want to provide timezone aware datetime objects we can use the 3rd party convenience library :mod:`pytz`.
        Mind that we need to fetch the timezone first and use `<timezone>.localize(<your datetime>)` to make it
        work correctly.

        Using `datetime(2017,6,1,23,59,0 tzinfo=<tz>)` does NOT work for most timezones with a
        daylight saving time. Check the `pytz <http://pythonhosted.org/pytz/#localized-times-and-date-arithmetic>`_
        documentation.

        To make it work using :mod:`pytz` and timezone aware :mod:`datetime` see the following example::

        >>> import pytz
        >>> start_date_tzaware = datetime.now(pytz.utc)
        >>> mytimezone = pytz.timezone('Europe/Amsterdam')
        >>> due_date_tzaware = mytimezone.localize(datetime(2019, 10, 27, 23, 59, 0))
        >>> project.edit(due_date=due_date_tzaware, start_date=start_date_tzaware)

        """
        update_dict = {'id': self.id}
        if name:
            if isinstance(name, (str, text_type)):
                update_dict.update({'name': name})
                self.name = name
            else:
                raise IllegalArgumentError('Name should be a string')

        if description:
            if isinstance(description, (str, text_type)):
                update_dict.update({'text': description})
                self.text = description
            else:
                raise IllegalArgumentError('Description should be a string')

        if start_date:
            if isinstance(start_date, datetime.datetime):
                if not start_date.tzinfo:
                    warnings.warn("The startdate '{}' is naive and not timezone aware, use pytz.timezone info. "
                                  "This date is interpreted as UTC time.".format(start_date.isoformat(sep=' ')))
                update_dict.update({'start_date': start_date.isoformat(sep='T')})
            else:
                raise IllegalArgumentError('Start date should be a datetime.datetime() object')

        if due_date:
            if isinstance(due_date, datetime.datetime):
                if not due_date.tzinfo:
                    warnings.warn("The duedate '{}' is naive and not timezone aware, use pytz.timezone info. "
                                  "This date is interpreted as UTC time.".format(due_date.isoformat(sep=' ')))
                update_dict.update({'due_date': due_date.isoformat(sep='T')})
            else:
                raise IllegalArgumentError('Due date should be a datetime.datetime() object')

        if status:
            if isinstance(status, (str, text_type)) and status in ScopeStatus.values():
                update_dict.update({'status': status})
            else:
                raise IllegalArgumentError('Status should be a string and in the list of acceptable '
                                           'status strings: {}'.format(ScopeStatus.values()))

        if tags:
            if isinstance(tags, (list, tuple, set)):
                update_dict.update({'tags': tags})
            else:
                raise IllegalArgumentError('tags should be a an array (list, tuple, set) of strings')

        if team:
            if isinstance(team, (str, text_type)) and is_uuid(team):
                update_dict.update({'team_id': team})
            else:
                raise IllegalArgumentError("team should be the uuid of a team")

        if options:
            if isinstance(options, (dict,)):
                update_dict.update({'options': options})
            else:
                raise IllegalArgumentError("options should be a dictionary")

        url = self._client._build_url('scope', scope_id=self.id)

        r = self._client._request('PUT', url, json=update_dict)

        if r.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update Scope ({})".format(r))
        else:
            self._json_data = r.json().get('results') and r.json().get('results')[0]
