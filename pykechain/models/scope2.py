from datetime import datetime
from typing import Union, Text, Dict, Optional, List  # noqa: F401

import requests

from pykechain.defaults import API_EXTRA_PARAMS
from pykechain.enums import Multiplicity, ScopeStatus, SubprocessDisplayMode, KEChainPages, ScopeRoles, \
    ScopeMemberActions
from pykechain.exceptions import APIError, NotFoundError, IllegalArgumentError
from pykechain.models.base import Base
from pykechain.models.input_checks import check_text, check_datetime, check_enum, check_list_of_text, \
    check_base, check_type
from pykechain.models.representations.component import RepresentationsComponent
from pykechain.models.sidebar.sidebar_manager import SideBarManager
from pykechain.models.tags import TagsMixin
from pykechain.models.team import Team
from pykechain.utils import parse_datetime, find


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

    def __init__(self, json: Dict, **kwargs) -> None:
        """Construct a scope from provided json data."""
        super().__init__(json, **kwargs)

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

        self._representations_container = RepresentationsComponent(
            self,
            self.options.get('representations', {}),
            self._save_representations,
        )

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
        super().refresh(json=json,
                        url=self._client._build_url('scope2', scope_id=self.id),
                        extra_params=API_EXTRA_PARAMS['scope2'])

    @property
    def representations(self):
        """Get and set the scope representations."""
        return self._representations_container.get_representations()

    @representations.setter
    def representations(self, value):
        self._representations_container.set_representations(value)

    def _save_representations(self, representation_options):
        options = self.options
        options.update({'representations': representation_options})
        self.options = options
    #
    # CRUD methods
    #

    def _update_scope_project_team(self, action, role, user):
        """
        Update the Project Team of the Scope. Updates include addition or removing of managers or members.

        :param action: type of action to be applied
        :type action: ScopeMemberActions
        :param role: type of role to be applied to the user
        :type role: ScopeRoles
        :param user: the username of the user to which the action applies to
        :type user: basestring
        :raises APIError: When unable to update the scope project team.
        """
        action = check_enum(action, ScopeMemberActions, 'action')
        role = check_enum(role, ScopeRoles, 'role')
        user = check_text(user, 'user')

        users = self._client._retrieve_users()['results']  # type: List[Dict]
        user_object = find(users, lambda u: u['username'] == user)  # type: Dict
        if user_object is None:
            raise NotFoundError('User "{}" does not exist'.format(user))

        url = self._client._build_url('scope2_{}_{}'.format(action, role), scope_id=self.id)

        response = self._client._request('PUT', url,
                                         params=API_EXTRA_PARAMS[self.__class__.__name__.lower()],
                                         data={'user_id': user_object['pk']})

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not {} {} in Scope".format(action, role), response=response)

        self.refresh(json=response.json().get('results')[0])

    def edit(
            self,
            name: Optional[Text] = None,
            description: Optional[Text] = None,
            start_date: Optional[datetime] = None,
            due_date: Optional[datetime] = None,
            status: Optional[Union[Text, ScopeStatus]] = None,
            tags: Optional[List[Text]] = None,
            team: Optional[Union[Team, Text]] = None,
            options: Optional[Dict] = None,
    ) -> None:
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
        ...              start_date=datetime.now(),  # naive time is interpreted as UTC time
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
        update_dict = {
            'id': self.id,
            'name': check_text(name, 'name') or self.name,
            'text': check_text(description, 'description') or self.description,
            'start_date': check_datetime(start_date, 'start_date'),
            'due_date': check_datetime(due_date, 'due_date'),
            'status': check_enum(status, ScopeStatus, 'status') or self.status,
        }
        team = check_base(team, Team, 'team', method=self._client.team)
        if team:
            update_dict['team_id'] = team
        tags = check_list_of_text(tags, 'tags', True)
        if tags is not None:
            update_dict['tags'] = tags
        scope_options = check_type(options, dict, 'options')
        if scope_options:
            update_dict['scope_options'] = scope_options

        url = self._client._build_url('scope2', scope_id=self.id)

        response = self._client._request('PUT', url,
                                         params=API_EXTRA_PARAMS[self.__class__.__name__.lower()],
                                         json=update_dict)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update Scope {}".format(self), response=response)

        self.refresh(json=response.json().get('results')[0])

        # TODO tags that are set are not in response
        if tags is not None:
            self._tags = tags

    def clone(self, **kwargs):
        """Clone a scope.

        See :method:`pykechain.Client.clone_scope()` for available parameters.
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
        return self._client.activities(*args, scope_id=self.id, **kwargs)

    def activity(self, *args, **kwargs):
        """Retrieve a single activity belonging to this scope.

        See :class:`pykechain.Client.activity` for available parameters.
        """
        return self._client.activity(*args, scope_id=self.id, **kwargs)

    def create_activity(self, *args, **kwargs):
        """Create a new activity belonging to this scope.

        See :class:`pykechain.Client.create_activity` for available parameters.
        """
        return self._client.create_activity(self.workflow_root, *args, **kwargs)

    def side_bar(self, *args, **kwargs) -> Optional[SideBarManager]:
        """Retrieve the side-bar manager."""
        return SideBarManager(scope=self, *args, **kwargs)

    def set_landing_page(self,
                         activity: Union['Activity2', KEChainPages],
                         task_display_mode: Optional[SubprocessDisplayMode] = SubprocessDisplayMode.ACTIVITIES,
                         ) -> None:
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

        check_enum(task_display_mode, SubprocessDisplayMode, 'task_display_mode')

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

    def members(self, is_manager: Optional[bool] = None, is_leadmember: Optional[bool] = None) -> List[Dict]:
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

    def add_member(self, member: Text) -> None:
        """
        Add a single member to the scope.

        You may only edit the list of members if the pykechain credentials allow this.

        :param member: single username to be added to the scope list of members
        :type member: basestring
        :raises APIError: when unable to update the scope member
        """
        self._update_scope_project_team(action=ScopeMemberActions.ADD, role=ScopeRoles.MEMBER, user=member)

    def remove_member(self, member: Text) -> None:
        """
        Remove a single member to the scope.

        :param member: single username to be removed from the scope list of members
        :type member: basestring
        :raises APIError: when unable to update the scope member
        """
        self._update_scope_project_team(action=ScopeMemberActions.REMOVE, role=ScopeRoles.MEMBER, user=member)

    def add_manager(self, manager: Text) -> None:
        """
        Add a single manager to the scope.

        :param manager: single username to be added to the scope list of managers
        :type manager: basestring
        :raises APIError: when unable to update the scope manager
        """
        self._update_scope_project_team(action=ScopeMemberActions.ADD, role=ScopeRoles.MANAGER, user=manager)

    def remove_manager(self, manager: Text) -> None:
        """
        Remove a single manager to the scope.

        :param manager: single username to be added to the scope list of managers
        :type manager: basestring
        :raises APIError: when unable to update the scope manager
        """
        self._update_scope_project_team(action=ScopeMemberActions.REMOVE, role=ScopeRoles.MANAGER, user=manager)

    def add_leadmember(self, leadmember: Text) -> None:
        """
        Add a single leadmember to the scope.

        :param leadmember: single username to be added to the scope list of leadmembers
        :type leadmember: basestring
        :raises APIError: when unable to update the scope leadmember
        """
        self._update_scope_project_team(action=ScopeMemberActions.ADD, role=ScopeRoles.LEADMEMBER, user=leadmember)

    def remove_leadmember(self, leadmember: Text) -> None:
        """
        Remove a single leadmember to the scope.

        :param leadmember: single username to be added to the scope list of leadmembers
        :type leadmember: basestring
        :raises APIError: when unable to update the scope leadmember
        """
        self._update_scope_project_team(action=ScopeMemberActions.REMOVE, role=ScopeRoles.LEADMEMBER, user=leadmember)
