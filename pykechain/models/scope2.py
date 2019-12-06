import datetime
import warnings
from typing import Any, Union, Text, Iterable, Dict, Optional, List  # noqa: F401

import requests
from six import text_type, string_types

from pykechain.defaults import API_EXTRA_PARAMS
from pykechain.enums import Multiplicity, ScopeStatus, SubprocessDisplayMode, KEChainPages
from pykechain.exceptions import APIError, NotFoundError, IllegalArgumentError
from pykechain.models.base import Base
from pykechain.models.sidebar.sidebar_manager import SideBarManager
from pykechain.models.tags import TagsMixin
from pykechain.models.team import Team
from pykechain.utils import parse_datetime, is_uuid


class Scope2(Base, TagsMixin):
    """A virtual object representing a KE-chain scope.

    :ivar id: id of the activity
    :type id: uuid
    :ivar name: name of the activity
    :type name: basestring
    :ivar created_at: created datetime of the activity
    :type created_at: datetime
    :ivar updated_at: updated datetime of the activity
    :type updated_at: datetime
    :ivar description: description of the activity
    :type description: basestring
    :ivar workflow_root: uuid of the workflow root object
    :type workflow_root: uuid
    :ivar status: status of the scope. One of :class:`pykechain.enums.ScopeStatus`
    :type status: basestring
    :ivar type: Type of the Scope. One of :class:`pykechain.enums.ScopeType` for WIM version 2
    :type type: basestring
    """

    def __init__(self, json, **kwargs):
        # type: (dict, **Any) -> None
        """Construct a scope from provided json data."""
        super(Scope2, self).__init__(json, **kwargs)

        # for 'kechain2.core.wim <2.0.0'
        self.process = json.get('process')
        # for 'kechain2.core.wim >=2.0.0'
        self.workflow_root = json.get('workflow_root_id')

        self.ref = json.get('ref')
        self.description = json.get('text')
        self.status = json.get('status')
        self.category = json.get('category')

        self._tags = json.get('tags')

        self.start_date = parse_datetime(json.get('start_date'))
        self.due_date = parse_datetime(json.get('due_date'))

    @property
    def bucket(self):
        """Bucket of the scope is deprecated in version 2.

        .. deprecated:: 3.0
           A `bucket` is a deprecated concept in KE-chain 3 backends. Use `scope_id` instead.
        """
        raise DeprecationWarning("Bucket has been deprecated in scope version 2")

    @property
    def team(self):
        """Team to which the scope is assigned."""
        team_dict = self._json_data.get('team_id_name')
        if team_dict and team_dict.get('id'):
            return self._client.team(pk=team_dict.get('id'))
        else:
            return None

    @property
    def options(self):
        """Options of the Scope.

        .. versionadded: 3.0
        """
        return self._json_data.get('scope_options')

    @options.setter
    def options(self, option_value):
        self.edit(options=option_value)

    def refresh(self, json=None, url=None, extra_params=None):
        """Refresh the object in place."""
        super(Scope2, self).refresh(json=json,
                                    url=self._client._build_url('scope2', scope_id=self.id),
                                    extra_params=API_EXTRA_PARAMS['scope2'])

    #
    # CRUD methods
    #

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
        if isinstance(user, (string_types, text_type)):
            users = self._client._retrieve_users()
            user_object = next((item for item in users['results'] if item["username"] == user), None)
            if user_object:
                url = self._client._build_url('scope2_{}'.format(select_action), scope_id=self.id)

                response = self._client._request('PUT', url,
                                                 params=API_EXTRA_PARAMS[self.__class__.__name__.lower()],
                                                 data={'user_id': user_object['pk']})
                if response.status_code != requests.codes.ok:  # pragma: no cover
                    raise APIError("Could not {} {} in Scope".format(select_action.split('_')[0], user_type))

                self._json_data = response.json().get('results')[0]
            else:
                raise NotFoundError("User {} does not exist".format(user))
        else:
            raise TypeError("User {} should be defined as a string".format(user))

    def _edit(self, update_dict):
        if update_dict.get('options'):
            update_dict['scope_options'] = update_dict.get('options')
            del update_dict['options']
        if update_dict.get('team'):
            update_dict['team_id'] = update_dict.get('team')
            del update_dict['team']

        url = self._client._build_url('scope2', scope_id=self.id)

        response = self._client._request('PUT', url, params=API_EXTRA_PARAMS[self.__class__.__name__.lower()],
                                         json=update_dict)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update Scope ({})".format(response))

        self.refresh(json=response.json().get('results')[0])

    def edit(self, name=None, description=None, start_date=None, due_date=None, status=None, tags=None, team=None,
             options=None):
        # type: (Text, Text, datetime.datetime, datetime.datetime, Union[ScopeStatus, Text], Iterable[Text], Team, Dict) -> None  # noqa: E501
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

        Examples
        --------
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

        To assign a scope to a team see the following example::

        >>> my_team = client.team(name='My own team')
        >>> project.edit(team=my_team)

        """
        update_dict = {'id': self.id}
        if name is not None:
            if isinstance(name, (str, text_type)):
                update_dict.update({'name': name})
                self.name = name
            else:
                raise IllegalArgumentError('Name should be a string')

        if description is not None:  # isinstance(description, (str, text_type)):
            if isinstance(description, (str, text_type)):
                update_dict.update({'text': description})
                self.text = description
            else:
                raise IllegalArgumentError('Description should be a string')

        if start_date is not None:
            if isinstance(start_date, datetime.datetime):
                if not start_date.tzinfo:
                    warnings.warn("The startdate '{}' is naive and not timezone aware, use pytz.timezone info. "
                                  "This date is interpreted as UTC time.".format(start_date.isoformat(sep=' ')))
                update_dict.update({'start_date': start_date.isoformat(sep='T')})
            else:
                raise IllegalArgumentError('Start date should be a datetime.datetime() object')

        if due_date is not None:
            if isinstance(due_date, datetime.datetime):
                if not due_date.tzinfo:
                    warnings.warn("The duedate '{}' is naive and not timezone aware, use pytz.timezone info. "
                                  "This date is interpreted as UTC time.".format(due_date.isoformat(sep=' ')))
                update_dict.update({'due_date': due_date.isoformat(sep='T')})
            else:
                raise IllegalArgumentError('Due date should be a datetime.datetime() object')

        if status is not None:
            if isinstance(status, (str, text_type)) and status in ScopeStatus.values():
                update_dict.update({'status': status})
            else:
                raise IllegalArgumentError('Status should be a string and in the list of acceptable '
                                           'status strings: {}'.format(ScopeStatus.values()))

        if tags is not None:
            if isinstance(tags, (list, tuple, set)):
                update_dict.update({'tags': tags})
            else:
                raise IllegalArgumentError('tags should be a an array (list, tuple, set) of strings')

        if team is not None:
            if isinstance(team, (str, text_type)) and is_uuid(team):
                update_dict.update({'team_id': team})
            elif isinstance(team, Team):
                update_dict.update({'team_id': team.id})
            else:
                raise IllegalArgumentError("team should be the uuid of a team")

        if options is not None:
            if isinstance(options, dict):
                update_dict.update({'options': options})
            else:
                raise IllegalArgumentError("options should be a dictionary")

        # do the update itself in an abstracted function.
        self._edit(update_dict)

    def clone(self, *args, **kwargs):
        """Clone a scope.

        See :method:`pykechain.Client.clone_scope()` for available paramters.
        """
        return self._client.clone_scope(source_scope=self, **kwargs)

    def delete(self, asynchronous=True):
        """Delete the scope.

        Only works with enough permissions.

        .. versionadded: 3.0

        See :method:`pykechain.Client.delete_scope()` for available parameters.
        :raises ForbiddenError: if you do not have the permissions to delete a scope
        """
        return self._client.delete_scope(scope=self, asynchronous=asynchronous)

    #
    # Part methods
    #

    def parts(self, *args, **kwargs):
        """Retrieve parts belonging to this scope.

        This uses

        See :class:`pykechain.Client.parts` for available parameters.
        """
        return self._client.parts(*args, scope_id=self.id, **kwargs)

    def part(self, *args, **kwargs):
        """Retrieve a single part belonging to this scope.

        See :class:`pykechain.Client.part` for available parameters.
        """
        return self._client.part(*args, scope_id=self.id, **kwargs)

    def properties(self, *args, **kwargs):
        """Retrieve properties belonging to this scope.

        .. versionadded: 3.0

        See :class:`pykechain.Client.properties` for available parameters.
        """
        return self._client.properties(*args, scope_id=self.id, **kwargs)

    def property(self, *args, **kwargs):
        """Retrieve a single property belonging to this scope.

        .. versionadded: 3.0

        See :class:`pykechain.Client.property` for available parameters.
        """
        return self._client.property(*args, scope_id=self.id, **kwargs)

    def model(self, *args, **kwargs):
        """Retrieve a single model belonging to this scope.

        See :class:`pykechain.Client.model` for available parameters.
        """
        return self._client.model(*args, scope_id=self.id, **kwargs)

    def create_model(self, parent, name, multiplicity=Multiplicity.ZERO_MANY):
        """Create a single part model in this scope.

        See :class:`pykechain.Client.create_model` for available parameters.
        """
        return self._client.create_model(parent, name, multiplicity=multiplicity)

    def create_model_with_properties(self, parent, name, multiplicity=Multiplicity.ZERO_MANY,
                                     properties_fvalues=None, **kwargs):
        """Create a model with its properties in a single API request.

        See :func:`pykechain.Client.create_model_with_properties()` for available parameters.
        """
        return self._client.create_model_with_properties(parent, name, multiplicity=multiplicity,
                                                         properties_fvalues=properties_fvalues, **kwargs)

    #
    # Activity methods
    #

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

    def side_bar(self, *args, **kwargs) -> Optional[SideBarManager]:
        """Retrieve the side-bar manager."""
        return SideBarManager(scope=self, *args, **kwargs)

    def set_landing_page(self,
                         activity: Union['Activity2', KEChainPages],
                         task_display_mode: Optional[SubprocessDisplayMode] = SubprocessDisplayMode.ACTIVITIES) -> None:
        """
        Update the landing page of the scope.

        :param activity: Activity2 object or KEChainPages option
        :type activity: (Activity2, KEChainPages)
        :param task_display_mode: display mode of the activity in KE-chain
        :type task_display_mode: SubprocessDisplayMode
        :return: None
        :rtype None
        """
        from pykechain.models import Activity2

        if not (isinstance(activity, Activity2) or activity in KEChainPages.values()):
            raise IllegalArgumentError(
                'activity must be of class Activity2 or a KEChainPages option, "{}" is not.'.format(activity))

        if task_display_mode not in SubprocessDisplayMode.values():
            raise IllegalArgumentError('task_display_mode must be a WorkBreakdownDisplayMode option, '
                                       '"{}" is not.'.format(task_display_mode))

        if isinstance(activity, Activity2):
            url = '#/scopes/{}/{}/{}'.format(self.id, task_display_mode, activity.id)
        else:
            url = '#/scopes/{}/{}'.format(self.id, activity)

        options = dict(self.options)
        options.update({'landingPage': url})
        self.options = options

    #
    # Service Methods
    #

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

    #
    # User and Members of the Scope
    #

    def members(self, is_manager=None, is_leadmember=None):
        # type: (Optional[bool], Optional[bool]) -> List[Dict]
        """
        Retrieve members of the scope.

        :param is_manager: (otional) set to True/False to filter members that are/aren't managers, resp.
        :type is_manager: bool
        :param is_leadmember: (optional) set to True/False to filter members that are/aren't leadmembers, resp.
        :type is_leadmember: bool
        :return: List of members, each defined as a dict

        Examples
        --------
        >>> members = project.members()
        >>> managers = project.members(is_manager=True)
        >>> leadmembers = project.members(is_leadmember=True)

        """
        members = [member for member in self._json_data['members'] if member['is_active']]

        if is_manager is not None:
            members = [member for member in members if member.get('is_manager') == is_manager]
        if is_leadmember is not None:
            members = [member for member in members if member.get('is_leadmember') == is_leadmember]

        return members

    def add_member(self, member):
        # type: (Text) -> None
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
        # type: (Text) -> None
        """
        Remove a single member to the scope.

        :param member: single username to be removed from the scope list of members
        :type member: basestring
        :raises APIError: when unable to update the scope member
        """
        select_action = 'remove_member'

        self._update_scope_project_team(select_action=select_action, user=member, user_type='member')

    def add_manager(self, manager):
        # type: (Text) -> None
        """
        Add a single manager to the scope.

        :param manager: single username to be added to the scope list of managers
        :type manager: basestring
        :raises APIError: when unable to update the scope manager
        """
        select_action = 'add_manager'

        self._update_scope_project_team(select_action=select_action, user=manager, user_type='manager')

    def remove_manager(self, manager):
        # type: (Text) -> None
        """
        Remove a single manager to the scope.

        :param manager: single username to be added to the scope list of managers
        :type manager: basestring
        :raises APIError: when unable to update the scope manager
        """
        select_action = 'remove_manager'

        self._update_scope_project_team(select_action=select_action, user=manager, user_type='manager')

    def add_leadmember(self, leadmember):
        # type: (Text) -> None
        """
        Add a single leadmember to the scope.

        :param leadmember: single username to be added to the scope list of leadmembers
        :type leadmember: basestring
        :raises APIError: when unable to update the scope leadmember
        """
        select_action = 'add_leadmember'

        self._update_scope_project_team(select_action=select_action, user=leadmember, user_type='leadmember')

    def remove_leadmember(self, leadmember):
        # type: (Text) -> None
        """
        Remove a single leadmember to the scope.

        :param leadmember: single username to be added to the scope list of leadmembers
        :type leadmember: basestring
        :raises APIError: when unable to update the scope leadmember
        """
        select_action = 'remove_leadmember'

        self._update_scope_project_team(select_action=select_action, user=leadmember, user_type='leadmember')
