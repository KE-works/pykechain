from datetime import datetime
from typing import Dict, List, Optional, Union  # noqa: F401

import requests

from pykechain.defaults import API_EXTRA_PARAMS
from pykechain.enums import (
    KEChainPages,
    Multiplicity,
    ScopeCategory,
    ScopeMemberActions,
    ScopeRoles,
    ScopeStatus,
    SubprocessDisplayMode,
)
from pykechain.exceptions import APIError, IllegalArgumentError, NotFoundError
from pykechain.models.activity import Activity
from pykechain.models.base import Base
from pykechain.models.context import Context
from pykechain.models.input_checks import (
    check_base,
    check_datetime,
    check_enum,
    check_list_of_text,
    check_text,
    check_type,
)
from pykechain.models.part import Part
from pykechain.models.property import Property
from pykechain.models.representations import BaseRepresentation
from pykechain.models.representations.component import RepresentationsComponent
from pykechain.models.service import Service, ServiceExecution
from pykechain.models.sidebar.sidebar_manager import SideBarManager
from pykechain.models.tags import TagsMixin
from pykechain.models.team import Team
from pykechain.models.workflow import Workflow
from pykechain.typing import ObjectID
from pykechain.utils import Empty, clean_empty_values, empty, find, is_uuid, parse_datetime


class Scope(Base, TagsMixin):
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
        self.process = json.get("process")
        # for 'kechain2.core.wim >=2.0.0'
        self.workflow_root = json.get("workflow_root_id")

        self._workflow_root_process = None
        self._catalog_root_process = None
        self._app_root_process = None
        self._product_root_model = None
        self._product_root_instance = None
        self._catalog_root_model = None
        self._catalog_root_instance = None

        self.ref = json.get("ref")
        self.description = json.get("text")
        self.status = json.get("status")
        self.category = json.get("category")

        self._tags = json.get("tags")

        self.start_date = parse_datetime(json.get("start_date"))
        self.due_date = parse_datetime(json.get("due_date"))

        self._representations_container = RepresentationsComponent(
            self,
            self.options.get("representations", {}),
            self._save_representations,
        )

    @property
    def team(self) -> Optional[Team]:
        """Team to which the scope is assigned."""
        team_dict = self._json_data.get("team_id_name")
        if team_dict and team_dict.get("id"):
            return self._client.team(pk=team_dict.get("id"))
        else:
            return None

    @property
    def options(self) -> Dict:
        """Options of the Scope.

        .. versionadded: 3.0
        """
        return self._json_data.get("scope_options")

    @options.setter
    def options(self, option_value):
        self.edit(options=option_value)

    def refresh(self, json=None, url=None, extra_params=None):
        """Refresh the object in place."""
        super().refresh(
            json=json,
            url=self._client._build_url("scope", scope_id=self.id),
            extra_params=API_EXTRA_PARAMS["scope"],
        )

    @property
    def representations(self) -> List["BaseRepresentation"]:
        """Get and set the scope representations."""
        return self._representations_container.get_representations()

    @representations.setter
    def representations(self, value):
        self._representations_container.set_representations(value)

    def _save_representations(self, representation_options):
        options = self.options
        options.update({"representations": representation_options})
        self.options = options

    @property
    def workflow_root_process(self) -> "Activity":
        """Retrieve the Activity root object with classification WORKFLOW."""
        if self._workflow_root_process is None:
            self._workflow_root_process = self.activity(
                id=self._json_data["workflow_root_id"]
            )
        return self._workflow_root_process

    @property
    def app_root_process(self) -> "Activity":
        """Retrieve the Activity root object with classification APP."""
        if self._app_root_process is None:
            self._app_root_process = self.activity(id=self._json_data["app_root_id"])
        return self._app_root_process

    @property
    def catalog_root_process(self) -> "Activity":
        """Retrieve the Activity root object with classification CATALOG."""
        if self._catalog_root_process is None:
            self._catalog_root_process = self.activity(
                id=self._json_data["catalog_root_id"]
            )
        return self._catalog_root_process

    @property
    def product_root_model(self) -> "Part":
        """Retrieve the Part root object with classification PRODUCT and category MODEL."""
        if self._product_root_model is None:
            self._product_root_model = self.model(
                id=self._json_data["product_model_id"]
            )
        return self._product_root_model

    @property
    def product_root_instance(self) -> "Part":
        """Retrieve the Part root object with classification PRODUCT and category INSTANCE."""
        if self._product_root_instance is None:
            self._product_root_instance = self.part(
                id=self._json_data["product_instance_id"]
            )
        return self._product_root_instance

    @property
    def catalog_root_model(self) -> "Part":
        """Retrieve the Part root object with classification CATALOG and category MODEL."""
        if self._catalog_root_model is None:
            self._catalog_root_model = self.model(
                id=self._json_data["catalog_model_id"]
            )
        return self._catalog_root_model

    @property
    def catalog_root_instance(self) -> "Part":
        """Retrieve the Part root object with classification CATALOG and category INSTANCE."""
        if self._catalog_root_instance is None:
            self._catalog_root_instance = self.part(
                id=self._json_data["catalog_instance_id"]
            )
        return self._catalog_root_instance

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
        action = check_enum(action, ScopeMemberActions, "action")
        role = check_enum(role, ScopeRoles, "role")
        user = check_text(user, "user")

        users: List[Dict] = self._client._retrieve_users()["results"]
        user_object: Dict = find(users, lambda u: u["username"] == user)
        if user_object is None:
            raise NotFoundError(f'User "{user}" does not exist')

        url = self._client._build_url(f"scope_{action}_{role}", scope_id=self.id)

        response = self._client._request(
            "PUT",
            url,
            params=API_EXTRA_PARAMS[self.__class__.__name__.lower()],
            data={"user_id": user_object["pk"]},
        )

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError(f"Could not {action} {role} in Scope", response=response)

        self.refresh(json=response.json().get("results")[0])

    def edit(
        self,
        name: Optional[Union[str, Empty]] = empty,
        description: Optional[Union[str, Empty]] = empty,
        start_date: Optional[Union[datetime, Empty]] = empty,
        due_date: Optional[Union[datetime, Empty]] = empty,
        status: Optional[Union[str, ScopeStatus, Empty]] = empty,
        category: Optional[Union[str, ScopeCategory, Empty]] = empty,
        tags: Optional[Union[List[str], Empty]] = empty,
        team: Optional[Union[Team, str, Empty]] = empty,
        options: Optional[Union[Dict, Empty]] = empty,
        **kwargs,
    ) -> None:
        """
        Edit the details of a scope.

        Setting an input to None will clear out the value (exception being name and status).

        :param name: (optionally) edit the name of the scope. Name cannot be cleared.
        :type name: basestring or None or Empty
        :param description: (optionally) edit the description of the scope or clear it
        :type description: basestring or None or Empty
        :param start_date: (optionally) edit the start date of the scope as a datetime object (UTC time/timezone
                            aware preferred) or clear it
        :type start_date: datetime or None or Empty
        :param due_date: (optionally) edit the due_date of the scope as a datetime object (UTC time/timzeone
                            aware preferred) or clear it
        :type due_date: datetime or None or Empty
        :param status: (optionally) edit the status of the scope as a string based. Status cannot be cleared.
        :type status: ScopeStatus or Empty
        :param category (optionally) edit the category of the scope
        :type category: ScopeCategory or Empty
        :param tags: (optionally) replace the tags on a scope, which is a list of strings ["one","two","three"] or
                    clear them
        :type tags: list of basestring or None or Empty
        :param team: (optionally) add the scope to a team. Team cannot be cleared.
        :type team: UUIDstring or None or Empty
        :param options: (optionally) custom options dictionary stored on the scope object
        :type options: dict or None or Empty

        :raises IllegalArgumentError: if the type of the inputs is not correct
        :raises APIError: if another Error occurs
        :warns: UserWarning - When a naive datetime is provided. Defaults to UTC.

        Examples
        --------
        >>> from datetime import datetime
        >>> project.edit(name='New project name',description='Changing the description just because I can',
        ... start_date=datetime.now(),status=ScopeStatus.CLOSED)

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
        >>> project.edit(start_date=start_date_tzaware,due_date=due_date_tzaware)

        To assign a scope to a team see the following example::

        >>> my_team = client.team(name='My own team')
        >>> project.edit(team=my_team)

        Not mentioning an input parameter in the function will leave it unchanged. Setting a parameter as None will
        clear its value (where that is possible). The example below will clear the due_date, but leave everything else
        unchanged.

        >>> project.edit(due_date=None)

        """
        update_dict = {
            "id": self.id,
            "name": check_text(name, "name") or self.name,
            "text": check_text(description, "description") or "",
            "start_date": check_datetime(start_date, "start_date"),
            "due_date": check_datetime(due_date, "due_date"),
            "status": check_enum(status, ScopeStatus, "status") or self.status,
            "category": check_enum(category, ScopeCategory, "category"),
            "tags": check_list_of_text(tags, "tags", True) or list(),
            "team_id": check_base(team, Team, "team") or "",
            "scope_options": check_type(options, dict, "options") or dict(),
        }

        if kwargs:  # pragma: no cover
            update_dict.update(kwargs)

        update_dict = clean_empty_values(update_dict=update_dict)

        url = self._client._build_url("scope", scope_id=self.id)

        response = self._client._request(
            "PUT",
            url,
            params=API_EXTRA_PARAMS[self.__class__.__name__.lower()],
            json=update_dict,
        )

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError(f"Could not update Scope {self}", response=response)

        self.refresh(json=response.json().get("results")[0])

        # TODO tags that are set are not in response
        if tags is not None and not isinstance(tags, Empty):
            self._tags = tags

    def clone(self, **kwargs) -> "Scope":
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

    def parts(self, *args, **kwargs) -> List["Part"]:
        """Retrieve parts belonging to this scope.

        This uses

        See :class:`pykechain.Client.parts` for available parameters.
        """
        return self._client.parts(*args, scope_id=self.id, **kwargs)

    def part(self, *args, **kwargs) -> "Part":
        """Retrieve a single part belonging to this scope.

        See :class:`pykechain.Client.part` for available parameters.
        """
        return self._client.part(*args, scope_id=self.id, **kwargs)

    def properties(self, *args, **kwargs) -> List["Property"]:
        """Retrieve properties belonging to this scope.

        .. versionadded: 3.0

        See :class:`pykechain.Client.properties` for available parameters.
        """
        return self._client.properties(*args, scope_id=self.id, **kwargs)

    def property(self, *args, **kwargs) -> "Property":
        """Retrieve a single property belonging to this scope.

        .. versionadded: 3.0

        See :class:`pykechain.Client.property` for available parameters.
        """
        return self._client.property(*args, scope_id=self.id, **kwargs)

    def model(self, *args, **kwargs) -> "Part":
        """Retrieve a single model belonging to this scope.

        See :class:`pykechain.Client.model` for available parameters.
        """
        return self._client.model(*args, scope_id=self.id, **kwargs)

    def create_model(self, parent, name, multiplicity=Multiplicity.ZERO_MANY) -> "Part":
        """Create a single part model in this scope.

        See :class:`pykechain.Client.create_model` for available parameters.
        """
        return self._client.create_model(parent, name, multiplicity=multiplicity)

    def create_model_with_properties(
        self,
        parent,
        name,
        multiplicity=Multiplicity.ZERO_MANY,
        properties_fvalues=None,
        **kwargs,
    ) -> "Part":
        """Create a model with its properties in a single API request.

        See :func:`pykechain.Client.create_model_with_properties()` for available parameters.
        """
        return self._client.create_model_with_properties(
            parent,
            name,
            multiplicity=multiplicity,
            properties_fvalues=properties_fvalues,
            **kwargs,
        )

    #
    # Activity methods
    #

    def activities(self, *args, **kwargs) -> List["Activity"]:
        """Retrieve activities belonging to this scope.

        See :class:`pykechain.Client.activities` for available parameters.
        """
        return self._client.activities(*args, scope=self.id, **kwargs)

    def activity(self, *args, **kwargs) -> "Activity":
        """Retrieve a single activity belonging to this scope.

        See :class:`pykechain.Client.activity` for available parameters.
        """
        return self._client.activity(*args, scope=self.id, **kwargs)

    def create_activity(self, *args, **kwargs) -> "Activity":
        """Create a new activity belonging to this scope.

        See :class:`pykechain.Client.create_activity` for available parameters.
        """
        return self._client.create_activity(self.workflow_root, *args, **kwargs)

    def side_bar(self, *args, **kwargs) -> Optional[SideBarManager]:
        """Retrieve the side-bar manager."""
        return SideBarManager(scope=self, *args, **kwargs)

    def set_landing_page(
        self,
        activity: Union["Activity", KEChainPages],
        task_display_mode: Optional[
            SubprocessDisplayMode
        ] = SubprocessDisplayMode.ACTIVITIES,
    ) -> None:
        """
        Update the landing page of the scope.

        :param activity: Activity object or KEChainPages option
        :type activity: (Activity, KEChainPages)
        :param task_display_mode: display mode of the activity in KE-chain
        :type task_display_mode: SubprocessDisplayMode
        :return: None
        :rtype None
        """
        from pykechain.models import Activity

        if not (isinstance(activity, Activity) or activity in KEChainPages.values()):
            raise IllegalArgumentError(
                'activity must be of class Activity or a KEChainPages option, "{}" is not.'.format(
                    activity
                )
            )

        check_enum(task_display_mode, SubprocessDisplayMode, "task_display_mode")

        if isinstance(activity, Activity):
            url = f"#/scopes/{self.id}/{task_display_mode}/{activity.id}"
        else:
            url = f"#/scopes/{self.id}/{activity}"

        options = dict(self.options)
        options.update({"landingPage": url})
        self.options = options

    def get_landing_page_url(self) -> Optional[str]:
        """
        Retrieve the landing page URL, if it is set in the options.

        :return: Landing page url
        """
        return self.options.get("landingPage")

    #
    # Service Methods
    #

    def services(self, *args, **kwargs) -> List["Service"]:
        """Retrieve services belonging to this scope.

        See :class:`pykechain.Client.services` for available parameters.

        .. versionadded:: 1.13
        """
        return self._client.services(*args, scope=self.id, **kwargs)

    def create_service(self, *args, **kwargs) -> "Service":
        """Create a service to current scope.

        See :class:`pykechain.Client.create_service` for available parameters.

        .. versionadded:: 1.13
        """
        return self._client.create_service(*args, scope=self.id, **kwargs)

    def service(self, *args, **kwargs) -> "Service":
        """Retrieve a single service belonging to this scope.

        See :class:`pykechain.Client.service` for available parameters.

        .. versionadded:: 1.13
        """
        return self._client.service(*args, scope=self.id, **kwargs)

    def service_executions(self, *args, **kwargs) -> List["ServiceExecution"]:
        """Retrieve services belonging to this scope.

        See :class:`pykechain.Client.service_executions` for available parameters.

        .. versionadded:: 1.13
        """
        return self._client.service_executions(*args, scope=self.id, **kwargs)

    def service_execution(self, *args, **kwargs) -> "ServiceExecution":
        """Retrieve a single service execution belonging to this scope.

        See :class:`pykechain.Client.service_execution` for available parameters.

        .. versionadded:: 1.13
        """
        return self._client.service_execution(*args, scope=self.id, **kwargs)

    #
    # User and Members of the Scope
    #

    def members(
        self,
        is_manager: Optional[bool] = None,
        is_supervisor: Optional[bool] = None,
        is_leadmember: Optional[bool] = None,
    ) -> List[Dict]:
        """
        Retrieve members of the scope.

        .. versionchanged:: 3.7
           we added the supervisor members for backend that support this.

        :param is_manager: (otional) set to True/False to filter members that are/aren't managers, resp.
        :type is_manager: bool
        :param is_supervisor: (optional) set to True/False to filter members that are/aren't supervisors, resp.
        :type is_supervisor: bool
        :param is_leadmember: (optional) set to True/False to filter members that are/aren't leadmembers, resp.
        :type is_leadmember: bool
        :return: List of members, each defined as a dict

        Examples
        --------
        >>> members = project.members()
        >>> managers = project.members(is_manager=True)
        >>> supervisors = project.members(is_supervisor=True)
        >>> leadmembers = project.members(is_leadmember=True)

        """
        members = [
            member for member in self._json_data["members"] if member["is_active"]
        ]

        if is_manager is not None:
            members = [
                member for member in members if member.get("is_manager") == is_manager
            ]
        if is_supervisor is not None:
            members = [
                member
                for member in members
                if member.get("is_supervisor") == is_supervisor
            ]
        if is_leadmember is not None:
            members = [
                member
                for member in members
                if member.get("is_leadmember") == is_leadmember
            ]
        return members

    def add_member(self, member: str) -> None:
        """
        Add a single member to the scope.

        You may only edit the list of members if the pykechain credentials allow this.

        :param member: single username to be added to the scope list of members
        :type member: basestring
        :raises APIError: when unable to update the scope member
        """
        self._update_scope_project_team(
            action=ScopeMemberActions.ADD, role=ScopeRoles.MEMBER, user=member
        )

    def remove_member(self, member: str) -> None:
        """
        Remove a single member to the scope.

        :param member: single username to be removed from the scope list of members
        :type member: basestring
        :raises APIError: when unable to update the scope member
        """
        self._update_scope_project_team(
            action=ScopeMemberActions.REMOVE, role=ScopeRoles.MEMBER, user=member
        )

    def add_manager(self, manager: str) -> None:
        """
        Add a single manager to the scope.

        :param manager: single username to be added to the scope list of managers
        :type manager: basestring
        :raises APIError: when unable to update the scope manager
        """
        self._update_scope_project_team(
            action=ScopeMemberActions.ADD, role=ScopeRoles.MANAGER, user=manager
        )

    def remove_manager(self, manager: str) -> None:
        """
        Remove a single manager to the scope.

        :param manager: single username to be added to the scope list of managers
        :type manager: basestring
        :raises APIError: when unable to update the scope manager
        """
        self._update_scope_project_team(
            action=ScopeMemberActions.REMOVE, role=ScopeRoles.MANAGER, user=manager
        )

    def add_leadmember(self, leadmember: str) -> None:
        """
        Add a single leadmember to the scope.

        :param leadmember: single username to be added to the scope list of leadmembers
        :type leadmember: basestring
        :raises APIError: when unable to update the scope leadmember
        """
        self._update_scope_project_team(
            action=ScopeMemberActions.ADD, role=ScopeRoles.LEADMEMBER, user=leadmember
        )

    def remove_leadmember(self, leadmember: str) -> None:
        """
        Remove a single leadmember to the scope.

        :param leadmember: single username to be added to the scope list of leadmembers
        :type leadmember: basestring
        :raises APIError: when unable to update the scope leadmember
        """
        self._update_scope_project_team(
            action=ScopeMemberActions.REMOVE,
            role=ScopeRoles.LEADMEMBER,
            user=leadmember,
        )

    def add_supervisor(self, supervisor: str) -> None:
        """
        Add a single supervisor to the scope.

        .. versionadded:: 3.7
           requires backend version 3.7 as well.

        :param supervisor: single username to be added to the scope list of supervisors
        :type supervisor: basestring
        :raises APIError: when unable to update the scope supervisor
        """
        if self._client.match_app_version(label="scope", version="<3.6.0"):
            raise NotImplementedError(
                "Adding and removal of supervisor members to a scope not "
                "possible with this backend version"
            )
        self._update_scope_project_team(
            action=ScopeMemberActions.ADD, role=ScopeRoles.SUPERVISOR, user=supervisor
        )

    def remove_supervisor(self, supervisor: str) -> None:
        """
        Remove a single supervisor to the scope.

        .. versionadded:: 3.7
           requires backend version 3.7 as well.

        :param supervisor: single username to be added to the scope list of supervisors
        :type supervisor: basestring
        :raises APIError: when unable to update the scope supervisor
        """
        if self._client.match_app_version(label="scope", version="<3.6.0"):
            raise NotImplementedError(
                "Adding and removal of supervisor members to a scope not "
                "possible with this backend version"
            )
        self._update_scope_project_team(
            action=ScopeMemberActions.REMOVE,
            role=ScopeRoles.SUPERVISOR,
            user=supervisor,
        )

    #
    # Context Methods
    #
    def context(self, *args, **kwargs) -> Context:
        """
        Retrieve a context object in this scope.

        See :class:`pykechain.Client.context` for available parameters.

        .. versionadded:: 3.11

        :return: a Context object
        """
        return self._client.context(*args, scope=self.id, **kwargs)

    def contexts(self, *args, **kwargs) -> List[Context]:
        """
        Retrieve one or more contexts object in this scope.

        See :class:`pykechain.Client.contexts` for available parameters.

        .. versionadded:: 3.11

        :return: a list of Context objects
        """
        return self._client.contexts(scope=self, **kwargs)

    def create_context(self, *args, **kwargs) -> Context:
        """
        Create a new Context object of a ContextType in a scope.

        See :class:`pykechain.Client.create_context` for available parameters.

        .. versionadded:: 3.11

        :return: a Context object
        """
        return self._client.create_context(scope=self, **kwargs)

    #
    # Forms Methods
    #
    def forms(self, **kwargs) -> List["Form"]:
        """
        Retrieve Form objects in a scope.

        See :class:`pykechain.Client.forms` for available parameters.

        :return: a list of Form objects
        """
        return self._client.forms(scope=self, **kwargs)

    def form(self, **kwargs) -> "Form":
        """
        Retrieve a Form object in a scope.

        See :class:`pykechain.Client.form` for available parameters.

        :return: a Form object
        """
        return self._client.form(scope=self, **kwargs)

    def create_form_model(self, *args, **kwargs) -> "Form":
        """
        Create a new Form object in a scope.

        See :class:`Form.create_model()` for available parameters.

        :return: a Form object
        """
        return self._client.create_form_model(*args, scope=self, **kwargs)

    def instantiate_form(self, model, *args, **kwargs) -> "Form":
        """
        Create a new Form instance based on a model.

        See the `Form.instantiate()` method for available arguments.

        :return: a created Form Instance
        """
        if self.id == model.scope_id:
            return self._client.instantiate_form(*args, model=model, *args, **kwargs)
        else:
            raise IllegalArgumentError(
                f"Form Model '{model.name}' not in Scope '{self.name}'"
            )

    #
    # Workflows Methods
    #
    def workflows(self, **kwargs) -> List["Workflow"]:
        """
        Retrieve Workflow objects in a scope.

        See :class:`pykechain.Client.workflows` for available parameters.

        :return: a list of Workflow objects
        """
        return self._client.workflows(scope=self, **kwargs)

    def workflow(self, **kwargs) -> "Workflow":
        """
        Retrieve a Workflow object in a scope.

        See :class:`pykechain.Client.workflow` for available parameters.

        :return: a Workflow object
        """
        return self._client.workflow(scope=self, **kwargs)

    def create_workflow(self, **kwargs) -> Workflow:
        """Create a new Defined Workflow object in this scope.

        See `Workflow.create_workflow` for available parameters.

        :return: a Workflow object
        """
        return Workflow.create(client=self._client, scope=self, **kwargs)

    def import_workflow(
        self, workflow: Union[Workflow, ObjectID], **kwargs
    ) -> "Workflow":
        """
        Import a Workflow object into the current scope.

        See :class:`Workflow.clone()` for available parameters.

        :return: a Workflow object
        """
        if is_uuid(workflow):
            workflow = self._client.workflow(pk=workflow)

        if isinstance(workflow, Workflow):
            return workflow.clone(target_scope=self, **kwargs)
        else:
            raise IllegalArgumentError(
                f"The workflow to import could not be found. I got: '{workflow}'"
            )
