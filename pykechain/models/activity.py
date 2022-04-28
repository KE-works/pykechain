import datetime
import os
import time
from typing import Dict, List, Optional, Union
from urllib.parse import urljoin

import requests

from pykechain.defaults import (
    API_EXTRA_PARAMS,
    ASYNC_REFRESH_INTERVAL,
    ASYNC_TIMEOUT_LIMIT,
)
from pykechain.enums import (
    ActivityClassification,
    ActivityRootNames,
    ActivityStatus,
    ActivityType,
    Category,
    PaperOrientation,
    PaperSize,
)
from pykechain.exceptions import (
    APIError,
    IllegalArgumentError,
    MultipleFoundError,
    NotFoundError,
    PDFDownloadTimeoutError,
)
from pykechain.models.input_checks import (
    check_base,
    check_datetime,
    check_enum,
    check_list_of_text,
    check_text,
    check_type,
    check_user,
)
from pykechain.models.representations.component import RepresentationsComponent
from pykechain.models.tags import TagsMixin
from pykechain.models.tree_traversal import TreeObject
from pykechain.models.user import User
from pykechain.models.widgets.widgets_manager import WidgetsManager
from pykechain.utils import (
    Empty,
    clean_empty_values,
    empty,
    get_offset_from_user_timezone,
    is_valid_email,
    parse_datetime,
)


class Activity(TreeObject, TagsMixin):
    """A virtual object representing a KE-chain activity.

    .. versionadded:: 2.0

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
    :ivar status: status of the activity. One of :class:`pykechain.enums.ActivityStatus`
    :type status: basestring
    :ivar classification: classification of the activity. One of :class:
        `pykechain.enums.ActivityClassification`
    :type classification: basestring
    :ivar activity_type: Type of the activity. One of :class:`pykechain.enums.ActivityType`
        for WIM version 2
    :type activity_type: basestring
    """

    def __init__(self, json, **kwargs):
        """Construct an Activity from a json object."""
        super().__init__(json, **kwargs)

        self._scope_id = json.get("scope_id")

        self.ref: str = json.get("ref")
        self.description: str = json.get("description", "")
        self.status: ActivityStatus = json.get("status")
        self.classification: ActivityClassification = json.get("classification")
        self.activity_type: ActivityType = json.get("activity_type")
        self.start_date = parse_datetime(json.get("start_date"))
        self.due_date = parse_datetime(json.get("due_date"))
        self.assignees_ids: List[str] = json.get("assignees_ids", [])
        self._options = json.get("activity_options", {})

        self._tags: List[str] = json.get("tags", [])
        self._representations_container = RepresentationsComponent(
            self,
            self._options.get("representations", {}),
            self._save_representations,
        )
        self._widgets_manager: Optional[WidgetsManager] = None

    def __call__(self, *args, **kwargs) -> "Activity":
        """Short-hand version of the `child` method."""
        return self.child(*args, **kwargs)

    def refresh(self, *args, **kwargs):
        """Refresh the object in place."""
        super().refresh(
            url=self._client._build_url("activity", activity_id=self.id),
            extra_params=API_EXTRA_PARAMS["activity"],
            *args,
            **kwargs,
        )

    #
    # additional properties
    #

    @property
    def assignees(self) -> List["User"]:
        """List of assignees to the activity.

        Provides a list of `User` objects or an empty list.

        :return: a list of `User` objects or an empty list.
        :rtype: list
        """
        return (
            self._client.users(id__in=self.assignees_ids, is_hidden=False)
            if self.assignees_ids
            else []
        )

    @property
    def scope_id(self):
        """
        Id of the scope this Activity belongs to.

        This property will always produce a scope_id, even when the scope object was not included
        in an earlier response.

        When the :class:`Scope` is not included in this task, it will make an additional call to
        the KE-chain API.

        :return: the scope id
        :type: uuid
        :raises NotFoundError: if the scope could not be found
        """
        if self._scope_id is None:
            self.refresh()
            if self._scope_id is None:
                raise NotFoundError(f"Activity '{self}' has no related scope!")
        return self._scope_id

    @scope_id.setter
    def scope_id(self, value):
        self._scope_id = value

    @property
    def representations(self):
        """Get and set the activity representations."""
        return self._representations_container.get_representations()

    @representations.setter
    def representations(self, value):
        self._representations_container.set_representations(value)

    def _save_representations(self, representation_options):
        self._options.update({"representations": representation_options})
        self.edit(activity_options=self._options)

    #
    # predicates
    #

    def is_rootlevel(self) -> bool:
        """
        Activity is at the toplevel of a project, i.e. below the root itself.

        It will look for the name of the parent which should be either
        ActivityRootNames.WORKFLOW_ROOT or ActivityRootNames.CATALOG_ROOT. If the name of the
        parent cannot be found an additional API call is made to retrieve the parent object (
        based on the `parent_id` in the json_data).

        :return: Return True if it is a root level activity, otherwise return False
        """
        # when the activity itself is a root, than return False immediately
        if self.is_root():
            return False

        parent_name = None
        parent_dict = self._json_data.get("parent_id_name")

        if parent_dict and "name" in parent_dict:
            parent_name = parent_dict.get("name")
        if not parent_dict:
            parent_name = self._client.activity(id=self.parent_id).name

        return parent_name in ActivityRootNames.values()

    def is_task(self) -> bool:
        """
        Activity is of ActivityType.TASK.

        :return: Return True if it is a task, otherwise return False
        """
        return self.activity_type == ActivityType.TASK

    def is_subprocess(self) -> bool:
        """
        Activity is of ActivityType.PROCESS.

        :return: Return True if it is a subprocess, otherwise return False
        """
        return self.is_process()

    def is_process(self) -> bool:
        """
        Activity is of ActivityType.PROCESS.

        :return: Return True if it is a process, otherwise return False
        """
        return self.activity_type == ActivityType.PROCESS

    def is_workflow(self) -> bool:
        """
        Classification of the Activity is of ActivityClassification.WORKFLOW.

        :return: Return True if it is a workflow classification activity, otherwise return False
        """
        return self.classification == ActivityClassification.WORKFLOW

    def is_app(self) -> bool:
        """
        Classification of the Activity is of ActivityClassification.APP.

        :return: Return True if it is a App classification activity, otherwise return False
        """
        return self.classification == ActivityClassification.APP

    def is_catalog(self) -> bool:
        """
        Classification of the Activity is of ActivityClassification.CATALOG.

        :return: Return True if it is a catalog classification activity, otherwise return False
        """
        return self.classification == ActivityClassification.CATALOG

    def is_workflow_root(self) -> bool:
        """
        Classification of the Activity is of ActivityClassification.WORKFLOW and a ROOT object.

        :return: Return True if it is a root workflow classification activity, otherwise False
        """
        return self.is_root() and self.is_workflow()

    def is_catalog_root(self) -> bool:
        """
        Classification of the Activity is of ActivityClassification.CATALOG and a ROOT object.

        :return: Return True if it is a root catalog classification activity, otherwise False
        """
        return self.is_root() and self.is_catalog()

    def is_root(self) -> bool:
        """
        Activity is a ROOT object.

        If you want to determine if it is also a workflow or a catalog root,
        use :func:`Activity.is_workflow_root()` or :func:`Activity.is_catalog_root()` methods.

        :return: Return True if it is a root object, otherwise return False
        """
        return self.name in ActivityRootNames.values() and self.parent_id is None

    def is_configured(self) -> bool:
        """
        Activity is configured with input and output properties.

        Makes an additional lightweight call to the API to determine if any associated models
        are there.

        :return: Return True if it is configured, otherwise return False
        """
        # check configured based on if we get at least 1 part back
        return bool(self.parts(category=Category.MODEL, limit=1))

    def is_customized(self) -> bool:
        """
        Activity is customized.

        In other words if it has a customization. Use can use the :func:`Activity.customization()`
        to retrieve the customization object and configure the task.

        :return: Return True if it is customized, otherwise return False
        """
        return bool(self._json_data.get("customization", False))

    #
    # methods
    #

    def create(self, *args, **kwargs) -> "Activity":
        """Create a new activity belonging to this subprocess.

        See :func:`pykechain.Client.create_activity` for available parameters.

        :raises IllegalArgumentError: if the `Activity` is not a `PROCESS`.
        :raises APIError: if an Error occurs.
        """
        if self.activity_type != ActivityType.PROCESS:
            raise IllegalArgumentError("One can only create a task under a subprocess.")
        return self._client.create_activity(self, *args, **kwargs)

    def parent(self) -> "Activity":
        """Retrieve the parent in which this activity is defined.

        If this is a task on top level, it raises NotFounderror.

        :return: a :class:`Activity`
        :raises NotFoundError: when it is a task in the top level of a project
        :raises APIError: when other error occurs

        Example
        -------
        >>> task = project.activity('Subtask')
        >>> parent_of_task = task.parent()

        """
        if self.parent_id is None:
            raise NotFoundError(
                f"Cannot find parent for task '{self}', as this task exist on top level."
            )
        elif self._parent is None:
            self._parent = self._client.activity(pk=self.parent_id, scope=self.scope_id)
        return self._parent

    def children(self, **kwargs) -> List["Activity"]:
        """Retrieve the direct activities of this subprocess.

        It returns a combination of Tasks (a.o. UserTasks) and Subprocesses on the direct
        descending level. Only when the activity is a Subprocess, otherwise it raises a
        NotFoundError

        :param kwargs: Additional search arguments, check :func:`pykechain.Client.activities`
            for additional info
        :return: a list of :class:`Activity`
        :raises NotFoundError: when this task is not of type `ActivityType.PROCESS`

        Example
        -------
        >>> task = project.activity('Subprocess')
        >>> children = task.children()

        Example searching for children of a subprocess which contains a name (icontains searches
        case insensitive)

        >>> task = project.activity('Subprocess')
        >>> children = task.children(name__icontains='more work')

        """
        if self.activity_type != ActivityType.PROCESS:
            raise NotFoundError(
                "Only subprocesses can have children, please choose a subprocess instead of a '{}'"
                " (activity '{}')".format(self.activity_type, self.name)
            )
        if not kwargs:
            if self._cached_children is None:
                self._cached_children = self._client.activities(
                    parent_id=self.id, scope=self.scope_id, **kwargs
                )
                for child in self._cached_children:
                    child._parent = self
            return self._cached_children
        else:
            return self._client.activities(
                parent_id=self.id, scope=self.scope_id, **kwargs
            )

    def child(
        self, name: Optional[str] = None, pk: Optional[str] = None, **kwargs
    ) -> "Activity":
        """
        Retrieve a child object.

        :param name: optional, name of the child
        :type name: str
        :param pk: optional, UUID of the child
        :type: pk: str
        :return: Child object
        :raises MultipleFoundError: whenever multiple children fit match inputs.
        :raises NotFoundError: whenever no child matching the inputs could be found.
        """
        if not (name or pk):
            raise IllegalArgumentError('You need to provide either "name" or "pk".')

        if self._cached_children:
            # First try to find the child without calling KE-chain.
            if name:
                activity_list = [c for c in self.children() if c.name == name]
            else:
                activity_list = [c for c in self.children() if c.id == pk]
        else:
            activity_list = []

        if not activity_list:
            if name:
                activity_list = self.children(name=name)
            else:
                activity_list = self.children(pk=pk)

        criteria = f"\nname: {name}\npk: {pk}\nkwargs: {kwargs}"

        if len(activity_list) == 1:
            child = activity_list[0]

        elif len(activity_list) > 1:
            raise MultipleFoundError(
                f"{self} has more than one matching child.{criteria}"
            )
        else:
            raise NotFoundError(f"{self} has no matching child.{criteria}")
        return child

    def siblings(self, **kwargs) -> List["Activity"]:
        """Retrieve the other activities that also belong to the parent.

        It returns a combination of Tasks (a.o. UserTasks) and Subprocesses on the level of the
        current task, including itself. This also works if the activity is of type
        `ActivityType.PROCESS`.

        :param kwargs: Additional search arguments, check :func:`pykechain.Client.activities`
            for additional info
        :return: list of :class:`Activity`
        :raises NotFoundError: when it is a task in the top level of a project

        Example
        -------
        >>> task = project.activity('Some Task')
        >>> siblings = task.siblings()

        Example for siblings containing certain words in the task name
        >>> task = project.activity('Some Task')
        >>> siblings = task.siblings(name__contains='Another Task')

        """
        if self.parent_id is None:
            raise NotFoundError(
                f"Cannot find siblings for task '{self}', as this task exist on top level."
            )
        return self._client.activities(
            parent_id=self.parent_id, scope=self.scope_id, **kwargs
        )

    def all_children(self) -> List["Activity"]:
        """
        Retrieve a flat list of all descendants, sorted depth-first.

        Returns an empty list for Activities of type TASK.

        :returns list of child objects
        :rtype List
        """
        if self.activity_type == ActivityType.TASK:
            return []
        return super().all_children()

    def count_children(self, **kwargs) -> int:
        """
        Retrieve the number of child activities using a light-weight request.

        :return: number of Activities
        :rtype int
        """
        if self.activity_type != ActivityType.PROCESS:
            raise IllegalArgumentError(
                "You can only count the number of children of an Activity of type"
                f" {ActivityType.PROCESS}"
            )

        return super().count_children(method="activities", **kwargs)

    def clone(
        self,
        parent: Optional[Union["Activity", str]] = None,
        update_dict: Optional[Dict] = None,
        **kwargs,
    ) -> Optional["Activity"]:
        """
        Create a copy of this activity.

        :param parent: (O) parent Activity object or UUID
        :type parent: Activity
        :param update_dict: (O) dictionary of new values to set on the cloned activities,
            e.g. `{"name": "New name"}`
        :type update_dict: dict
        :param kwargs: additional arguments, see the `Client.clone_activities()` method
        :return: clone of this activity
        :rtype Activity
        """
        update_dict = check_type(update_dict, dict, "update_dict")
        if update_dict:
            validated_dict = self._validate_edit_arguments({}, **update_dict)
        else:
            validated_dict = None

        cloned_activities = self._client.clone_activities(
            activity_parent=check_base(parent, Activity, "parent") or self.parent_id,
            activities=[self],
            activity_update_dicts={self.id: validated_dict} if validated_dict else None,
            **kwargs,
        )
        return cloned_activities[0] if cloned_activities else None

    def edit_cascade_down(
        self,
        start_date: Optional[Union[datetime.datetime, Empty]] = empty,
        due_date: Optional[Union[datetime.datetime, Empty]] = empty,
        assignees: Optional[Union[List[str], Empty]] = empty,
        assignees_ids: Optional[Union[List[str], Empty]] = empty,
        status: Optional[Union[ActivityStatus, str, Empty]] = empty,
        overwrite: Optional[bool] = False,
        **kwargs,
    ) -> None:
        """
        Edit the activity and all its descendants with a single operation.

        :param start_date: (optionally) edit the start date of the activity as a datetime object
            (UTC time/timezone aware preferred)
        :type start_date: datetime or None
        :param due_date: (optionally) edit the due_date of the activity as a datetime object
            (UTC time/timzeone aware preferred)
        :type due_date: datetime or None
        :param assignees: (optionally) edit the assignees (usernames) of the activity as a list
        :type assignees: list(basestring) or None
        :param assignees_ids: (optionally) edit the assignees (user id's) of the activity as a list
        :type assignees_ids: list(basestring) or None
        :param status: (optionally) edit the status of the activity as a string based
            on :class:`~pykechain.enums.ActivityStatus`
        :type status: ActivityStatus, basestring or None
        :param overwrite: (optionally) whether to overwrite existing assignees (True) or
            merge with existing assignees (False, default)
        :type overwrite: bool

        :return: flat list of the current task all descendants that have been edited
        :rtype list[Activity]
        """
        update_dict = {"id": self.id}

        self._validate_edit_arguments(
            update_dict=update_dict,
            start_date=start_date,
            due_date=due_date,
            assignees=assignees,
            assignees_ids=assignees_ids,
            status=status,
            **kwargs,
        )

        all_tasks = [self] + self.all_children()
        new_assignees = update_dict.get("assignees_ids", list())

        # Create update-json
        data = list()

        update_dict = clean_empty_values(update_dict=update_dict)

        for task in all_tasks:
            task_specific_update_dict = dict(update_dict)

            if not overwrite:
                # Append the existing assignees of the task to the new assignees
                existing_assignees = [u.id for u in task.assignees]
                task_specific_update_dict["assignees_ids"] = list(
                    set(existing_assignees + new_assignees)
                )

            task_specific_update_dict.update({"id": task.id})
            data.append(task_specific_update_dict)

        # Perform bulk update
        self._client.update_activities(activities=data)

    def edit(
        self,
        name: Optional[Union[str, Empty]] = empty,
        description: Optional[Union[str, Empty]] = empty,
        start_date: Optional[Union[datetime.datetime, Empty]] = empty,
        due_date: Optional[Union[datetime.datetime, Empty]] = empty,
        assignees: Optional[Union[List[str], Empty]] = empty,
        assignees_ids: Optional[Union[List[str], Empty]] = empty,
        status: Optional[Union[ActivityStatus, str, Empty]] = empty,
        tags: Optional[Union[List[str], Empty]] = empty,
        **kwargs,
    ) -> None:
        """Edit the details of an activity.

        Setting an input to None will clear out the value (exception being name and status).

        :param name: (optionally) edit the name of the activity. Name cannot be cleared.
        :type name: basestring or None or Empty
        :param description: (optionally) edit the description of the activity or clear it
        :type description: basestring or None or Empty
        :param start_date: (optionally) edit the start date of the activity as a datetime object
            (UTC time/timezone aware preferred) or clear it
        :type start_date: datetime or None or Empty
        :param due_date: (optionally) edit the due_date of the activity as a datetime object
            (UTC time/timzeone aware preferred) or clear it
        :type due_date: datetime or None or Empty
        :param assignees: (optionally) edit the assignees (usernames) of the activity as a list,
            will overwrite all assignees or clear them
        :type assignees: list(basestring) or None or Empty
        :param assignees_ids: (optionally) edit the assignees (user id's) of the activity as a
            list, will overwrite all assignees or clear them
        :type assignees_ids: list(basestring) or None or Empty
        :param status: (optionally) edit the status of the activity as a string based. Status
            cannot be cleared on :class:`~pykechain.enums.ActivityStatus`
        :type status: ActivityStatus or None or Empty
        :param tags: (optionally) replace the tags on an activity, which is a list of strings
            ["one","two","three"] or clear them
        :type tags: list of basestring or None or Empty

        :raises NotFoundError: if a `username` in the list of assignees is not in the list
            of scope members
        :raises IllegalArgumentError: if the type of the inputs is not correct
        :raises APIError: if another Error occurs
        :warns: UserWarning - When a naive datetime is provided. Defaults to UTC.

        Example
        -------
        >>> from datetime import datetime
        >>> my_task = project.activity('Specify the wheel diameter')
        >>> my_task.edit(name='Specify wheel diameter and circumference',
        ...     description='The diameter and circumference are specified in inches',
        ...     start_date=datetime.utcnow(),
        ...     assignee='testuser')

        If we want to provide timezone aware datetime objects we can use the 3rd party
        convenience library :mod:`pytz`. Mind that we need to fetch the timezone first and use
        `<timezone>.localize(<your datetime>)` to make it work correctly.

        Using `datetime(2017,6,1,23,59,0 tzinfo=<tz>)` does NOT work for most timezones with a
        daylight saving time. Check the `pytz
        <http://pythonhosted.org/pytz/#localized-times-and-date-arithmetic>`_ documentation.

        To make it work using :mod:`pytz` and timezone aware :mod:`datetime` see the following
        example::

        >>> import pytz
        >>> start_date_tzaware = datetime.now(pytz.utc)
        >>> mytimezone = pytz.timezone('Europe/Amsterdam')
        >>> due_date_tzaware = mytimezone.localize(datetime(2019, 10, 27, 23, 59, 0))
        >>> my_task.edit(start_date=start_date_tzaware,due_date=due_date_tzaware)

        Not mentioning an input parameter in the function will leave it unchanged. Setting a
        parameter as None will clear its value (where that is possible). The example below will
        clear the due_date, but leave everything else unchanged.

        >>> my_task.edit(due_date=None)

        """
        update_dict = {
            "id": self.id,
            "name": check_text(text=name, key="name") or self.name,
            "description": check_text(text=description, key="description") or "",
            "tags": check_list_of_text(tags, "tags", True) or list(),
        }

        self._validate_edit_arguments(
            update_dict=update_dict,
            start_date=start_date,
            due_date=due_date,
            assignees=assignees,
            assignees_ids=assignees_ids,
            status=status,
            **kwargs,
        )

        update_dict = clean_empty_values(update_dict=update_dict)

        url = self._client._build_url("activity", activity_id=self.id)

        response = self._client._request(
            "PUT", url, json=update_dict, params=API_EXTRA_PARAMS["activity"]
        )

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError(f"Could not update Activity {self}", response=response)

        self.refresh(json=response.json().get("results")[0])

    def _validate_edit_arguments(
        self,
        update_dict,
        start_date=None,
        due_date=None,
        assignees=None,
        assignees_ids=None,
        status=None,
        **kwargs,
    ) -> Dict:
        """Verify inputs provided in both the `clone`, `edit` and `edit_cascade_down` methods."""
        update_dict.update(
            {
                "start_date": check_datetime(dt=start_date, key="start_date"),
                "due_date": check_datetime(dt=due_date, key="due_date"),
                "status": check_enum(status, ActivityStatus, "status") or self.status,
            }
        )

        # If both are empty that means the user is not interested in changing them
        if isinstance(assignees_ids, Empty) and isinstance(assignees, Empty):
            pass

        # If one of them is None, then the assignees will be cleared from the Activity
        elif assignees is None or assignees_ids is None:
            update_dict["assignees_ids"] = list()

        # In case both of them have values specified, then an Error is raised
        elif (
            assignees
            and assignees_ids
            and not isinstance(assignees, Empty)
            and not isinstance(assignees_ids, Empty)
        ):
            raise IllegalArgumentError(
                "Provide either assignee names or their ids, but not both."
            )
        # Otherwise, pick the one that has a value specified which is not Empty
        else:
            assignees = (
                assignees
                if assignees is not None and not isinstance(assignees, Empty)
                else assignees_ids
            )

            if assignees:
                if not isinstance(assignees, (list, tuple, set)) or not all(
                    isinstance(a, (str, int)) for a in assignees
                ):
                    raise IllegalArgumentError(
                        "All assignees must be provided as list, tuple or set of names or IDs."
                    )

                update_assignees_ids = [
                    m.get("id")
                    for m in self.scope.members()
                    if m.get("id") in assignees or m.get("username") in set(assignees)
                ]

                if len(update_assignees_ids) != len(assignees):
                    raise NotFoundError(
                        "All assignees should be a member of the project."
                    )
            else:
                update_assignees_ids = list()

            update_dict["assignees_ids"] = update_assignees_ids

        if kwargs:
            update_dict.update(kwargs)

        return update_dict

    def delete(self) -> bool:
        """Delete this activity.

        :return: True when successful
        :raises APIError: when unable to delete the activity
        """
        response = self._client._request(
            "DELETE", self._client._build_url("activity", activity_id=self.id)
        )

        if response.status_code != requests.codes.no_content:
            raise APIError(f"Could not delete Activity {self}.", response=response)
        return True

    #
    # Searchers and retrievers
    #

    def parts(self, *args, **kwargs):
        """Retrieve parts belonging to this activity.

        Without any arguments it retrieves the Instances related to this task only.

        This call only returns the configured properties in an activity. So properties that are
        not configured are not in the returned parts.

        See :class:`pykechain.Client.parts` for additional available parameters.

        Example
        -------
        >>> task = project.activity('Specify Wheel Diameter')
        >>> parts = task.parts()

        To retrieve the models only.
        >>> parts = task.parts(category=Category.MODEL)

        """
        return [p for w in self.widgets() for p in w.parts(*args, **kwargs)]

    def associated_parts(self, *args, **kwargs):
        """Retrieve models and instances belonging to this activity.

        This is a convenience method for the :func:`Activity.parts()` method, which is used to
        retrieve both the `Category.MODEL` as well as the `Category.INSTANCE` in a tuple.

        This call only returns the configured properties in an activity. So properties that are
        not configured are not in the returned parts.

        If you want to retrieve only the models associated to this task it is better to use:
            `task.parts(category=Category.MODEL)`.

        See :func:`pykechain.Client.parts` for additional available parameters.

        :returns: a tuple(models of :class:`PartSet`, instances of :class:`PartSet`)

        Example
        -------
        >>> task = project.activity('Specify Wheel Diameter')
        >>> all_models, all_instances = task.associated_parts()

        """
        associated_models = list()
        associated_instances = list()
        for widget in self.widgets():
            associated_models.extend(
                widget.parts(category=Category.MODEL, *args, **kwargs)
            )
            associated_instances.extend(
                widget.parts(category=Category.INSTANCE, *args, **kwargs)
            )

        return (associated_models, associated_instances)

    def associated_object_ids(self) -> List[Dict]:
        """Retrieve object ids associated to this activity.

        This represents a more in-depth retrieval of objects associated to the activity. Each
        element in the list represents a `Property` of `Category.INSTANCE`. Each element
        contains the following fields:

        'id': The ID of the association
        'widget': The ID of the widget to which the Property instance is associated
        'activity': The ID of the activity
        'model_property': The ID of the Property model
        'model_part': The ID of the model of the Part containing said Property
        'instance_property': The ID of the Property instance
        'instance_part': The ID of the Part instance containing said Property
        'writable': True if the Property is writable, False if is not

        See :func:`pykechain.Client.parts` for additional available parameters.

        :returns: a list of dictonaries with association objects associated to the activity
        :raises NotFoundError: When the response from the server was invalid.

        Example
        -------
        >>> task = project.activity('Specify Wheel Diameter')
        >>> associated_object_ids = task.associated_object_ids()

        """
        request_params = dict(
            activity=self.id,
        )

        url = self._client._build_url("associations")

        response = self._client._request("GET", url, params=request_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError(
                f"Could not retrieve Associations on Activity {self}", response=response
            )

        data = response.json()
        return data["results"]

    #
    # Customizations
    #

    def widgets(self, **kwargs) -> "WidgetsManager":
        """
        Widgets of the activity.

        Works with KE-chain version 3.

        :param kwargs: additional keyword arguments
        :return: A :class:`WidgetManager` list, containing the widgets
        :rtype: WidgetManager
        :raises NotFoundError: when the widgets could not be found
        :raises APIError: when the API does not support the widgets, or when API gives an error.
        """
        if self._widgets_manager is None:
            widgets = self._client.widgets(activity=self.id, **kwargs)
            self._widgets_manager = WidgetsManager(widgets=widgets, activity=self)
        return self._widgets_manager

    def download_as_pdf(
        self,
        target_dir: str = None,
        pdf_filename: str = None,
        paper_size: PaperSize = PaperSize.A4,
        paper_orientation: PaperOrientation = PaperOrientation.PORTRAIT,
        include_appendices: bool = False,
        include_qr_code: bool = False,
        user: Optional[User] = None,
        timeout: int = ASYNC_TIMEOUT_LIMIT,
    ) -> str:
        """
        Retrieve the PDF of the Activity.

        .. versionadded:: 2.1

        :param target_dir: (optional) directory path name where the store the log.txt to.
        :param pdf_filename: (optional) log filename to write the log to, defaults to `log.txt`.
        :param paper_size: The size of the paper to which the PDF is downloaded:
                               - a4paper (default): A4 paper size
                               - a3paper: A3 paper size
                               - a2paper: A2 paper size
                               - a1paper: A1 paper size
                               - a0paper: A0 paper size
        :param paper_orientation: The orientation of the paper to which the PDF is downloaded:
                               - portrait (default): portrait orientation
                               - landscape: landscape orientation
        :param include_appendices: True if the PDF should contain appendices, False (default)
            if otherwise.
        :param include_qr_code: True if the PDF should include a QR-code, False (default)
            if otherwise.
        :param user: (optional) used to calculate the offset needed to interpret Datetime
            Properties. Not having a user will simply use the default UTC.
        :param timeout: (optional) number of seconds to wait for the PDF to be created, defaults
            to ASYNC_TIMEOUT_LIMIT
        :raises APIError: if the pdf file could not be found.
        :raises OSError: if the file could not be written.
        :returns Path to the saved pdf file
        :rtype str
        """
        if not pdf_filename:
            pdf_filename = self.name + ".pdf"
        if not pdf_filename.endswith(".pdf"):
            pdf_filename += ".pdf"

        full_path = os.path.join(target_dir or os.getcwd(), pdf_filename)

        request_params = dict(
            papersize=check_enum(paper_size, PaperSize, "paper_size"),
            orientation=check_enum(
                paper_orientation, PaperOrientation, "paper_orientation"
            ),
            appendices=check_type(include_appendices, bool, "include_appendices"),
            includeqr=check_type(include_qr_code, bool, "include_qr_code"),
        )

        if user:
            user_object = check_type(user, User, "user")
            request_params.update(
                offset=get_offset_from_user_timezone(user=user_object)
            )

        url = self._client._build_url("activity_export", activity_id=self.id)
        response = self._client._request("GET", url, params=request_params)
        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError(
                f"Could not download PDF of Activity {self}", response=response
            )

        # If appendices are included, the request becomes asynchronous
        if include_appendices:  # pragma: no cover
            data = response.json()

            # Download the pdf async
            url = urljoin(self._client.api_root, data["download_url"])

            count = 0
            while count <= timeout:
                response = self._client._request("GET", url=url)

                if response.status_code == requests.codes.ok:  # pragma: no cover
                    with open(full_path, "wb") as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                    return full_path

                count += ASYNC_REFRESH_INTERVAL
                time.sleep(ASYNC_REFRESH_INTERVAL)

            raise PDFDownloadTimeoutError(
                f"Could not download PDF of Activity {self} within the time-out limit "
                f"of {timeout} seconds",
                response=response,
            )

        with open(full_path, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)

        return full_path

    def move(self, parent, classification=None):
        """
        Move the `Activity` to a new parent.

        See :func:`pykechain.Client.move_activity` for available parameters.

        If you want to move an Activity from one classification to another, you need to provide
        the target classification. The classification of the parent should match the one
        provided in the function. This is to ensure that you really want this to happen.

        :param parent: parent object to move activity to
        :type parent: Union[Activity, Text]
        :param classification: (optional) classification of the target parent if you want to
            change the classification.
        :type classification: ActivityClassification or None
        :raises IllegalArgumentError: if the 'parent' activity_type is not
            :class:`enums.ActivityType.SUBPROCESS`
        :raises IllegalArgumentError: if the 'parent' type is not :class:`Activity` or UUID
        :raises APIError: if an Error occurs.
        """
        return self._client.move_activity(self, parent, classification=classification)

    def share_link(
        self,
        subject: str,
        message: str,
        recipient_users: List[Union[User, str]],
        from_user: Optional[User] = None,
    ) -> None:
        """
        Share the link of the `Activity` through email.

        :param subject: subject of email
        :type subject: basestring
        :param message: message of email
        :type message: basestring
        :param recipient_users: users that will receive the email
        :type recipient_users: list(Union(User, Id))
        :param from_user: User that shared the link (optional)
        :type from_user: User object
        :raises APIError: if an internal server error occurred.
        """
        params = dict(
            message=check_text(message, "message"),
            subject=check_text(subject, "subject"),
            recipient_users=[
                check_user(recipient, User, "recipient")
                for recipient in recipient_users
            ],
            activity_id=self.id,
        )

        if from_user:
            check_user(from_user, User, "from_user")
            params.update(
                from_user=from_user.id,
                offset=get_offset_from_user_timezone(user=from_user),
            )

        url = self._client._build_url("notification_share_activity_link")

        response = self._client._request("POST", url, data=params)

        if response.status_code not in (
            requests.codes.created,
            requests.codes.accepted,
        ):  # pragma: no cover
            raise APIError(
                f"Could not share the link to Activity {self}", response=response
            )

    def share_pdf(
        self,
        subject: str,
        message: str,
        recipient_users: List[Union[User, str]],
        paper_size: Optional[PaperSize] = PaperSize.A3,
        paper_orientation: Optional[PaperOrientation] = PaperOrientation.PORTRAIT,
        from_user: Optional[User] = None,
        include_appendices: Optional[bool] = False,
        include_qr_code: Optional[bool] = False,
        **kwargs,
    ) -> None:
        """
        Share the PDF of the `Activity` through email.

        :param subject: subject of email
        :type subject: basestring
        :param message: message of email
        :type message: basestring
        :param recipient_users: users that will receive the email
        :type recipient_users: list(Union(User, Id))
        :param paper_size: The size of the paper to which the PDF is downloaded:
                               - a4paper: A4 paper size
                               - a3paper: A3 paper size (default)
                               - a2paper: A2 paper size
                               - a1paper: A1 paper size
                               - a0paper: A0 paper size
        :type paper_size: basestring (see :class:`enums.PaperSize`)
        :param paper_orientation: The orientation of the paper to which the PDF is downloaded:
                               - portrait (default): portrait orientation
                               - landscape: landscape orientation
        :type paper_size: basestring (see :class:`enums.PaperOrientation`)
        :param from_user: User that shared the PDF (optional)
        :type from_user: User object
        :param include_appendices: True if the PDF should contain appendices, False (default)
            if otherwise.
        :type include_appendices: bool
        :param include_qr_code: True if the PDF should include a QR-code, False (default)
            if otherwise.
        :type include_qr_code: bool
        :raises APIError: if an internal server error occurred.
        """
        recipient_emails = list()
        recipient_users_ids = list()
        if isinstance(recipient_users, list) and all(
            isinstance(r, (str, int, User)) for r in recipient_users
        ):
            for user in recipient_users:
                if is_valid_email(user):
                    recipient_emails.append(user)
                else:
                    recipient_users_ids.append(check_user(user, User, "recipient"))
        else:
            raise IllegalArgumentError(
                "`recipients` must be a list of User objects, IDs or email addresses, "
                '"{}" ({}) is not.'.format(recipient_users, type(recipient_users))
            )

        params = dict(
            message=check_text(message, "message"),
            subject=check_text(subject, "subject"),
            recipient_users=recipient_users_ids,
            recipient_emails=recipient_emails,
            activity_id=self.id,
            papersize=check_enum(paper_size, PaperSize, "paper_size"),
            orientation=check_enum(
                paper_orientation, PaperOrientation, "paper_orientation"
            ),
            appendices=check_type(include_appendices, bool, "include_appendices"),
            includeqr=check_type(include_qr_code, bool, "include_qr_code"),
        )

        if from_user:
            check_user(from_user, User, "from_user")
            params.update(
                from_user=from_user.id,
                offset=get_offset_from_user_timezone(user=from_user),
            )

        url = self._client._build_url("notification_share_activity_pdf")

        response = self._client._request("POST", url, data=params)

        if response.status_code not in (
            requests.codes.created,
            requests.codes.accepted,
        ):  # pragma: no cover
            raise APIError(
                f"Could not share the link to Activity {self}", response=response
            )

    #
    # Context Methods
    #
    def context(self, *args, **kwargs) -> "Context":
        """
        Retrieve a context object associated to this activity and scope.

        See :class:`pykechain.Client.context` for available parameters.

        .. versionadded:: 3.12

        :return: a Context object
        """
        return self._client.context(*args, scope=self.scope, activity=self, **kwargs)

    def contexts(self, *args, **kwargs) -> List["Context"]:
        """
        Retrieve context objects t associated to this activity and scope.

        See :class:`pykechain.Client.contexts` for available parameters.

        .. versionadded:: 3.12

        :return: a list of Context objects
        """
        return self._client.contexts(scope=self.scope, activity=self, **kwargs)

    def create_context(self, *args, **kwargs) -> "Context":
        """
        Create a new Context object of a ContextType in a scope and associated it to this activity.

        See :class:`pykechain.Client.create_context` for available parameters.

        .. versionadded:: 3.12

        :return: a Context object
        """
        return self._client.create_context(
            scope=self.scope, actitivities=[self], **kwargs
        )

    def link_context(self, context: "Context") -> None:
        """
        Link the current activity to an existing Context.

        If you want to link multiple activities at once,
        use the `Context.link_activities()` method.

        :param context: A Context object to link the current activity to.
        :raises IllegalArgumentError: When the context is not a Context object.
        """
        if not context.__class__.__name__ == "Context":
            raise IllegalArgumentError(
                f"`context` should be a proper Context object. Got: {context}"
            )
        context.link_activities(activities=[self])
        self.refresh()

    def unlink_context(self, context: "Context") -> None:
        """
        Link the current activity to an existing Context.

        If you want to unlink multiple activities at once,
        use the `Context.unlink_activities()` method.

        :param context: A Context object to unlink the current activity from.
        :raises IllegalArgumentError: When the context is not a Context object.
        """
        if not context.__class__.__name__ == "Context":
            raise IllegalArgumentError(
                f"`context` should be a proper Context object. Got: {context}"
            )
        context.unlink_activities(activities=[self])
        self.refresh()
