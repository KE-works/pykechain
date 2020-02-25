import datetime
import os
import time
import warnings
from typing import List, Text, Dict, Optional, Union

import requests
from requests.compat import urljoin  # type: ignore
from six import text_type

from pykechain.defaults import ASYNC_REFRESH_INTERVAL, ASYNC_TIMEOUT_LIMIT, API_EXTRA_PARAMS
from pykechain.enums import ActivityType, ActivityStatus, Category, ActivityClassification, ActivityRootNames, \
    PaperSize, PaperOrientation
from pykechain.exceptions import NotFoundError, IllegalArgumentError, APIError, MultipleFoundError
from pykechain.models.tags import TagsMixin
from pykechain.models.tree_traversal import TreeObject
from pykechain.models.widgets.widgets_manager import WidgetsManager
from pykechain.utils import is_uuid, parse_datetime


class Activity2(TreeObject, TagsMixin):
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
    :ivar classification: classification of the activity. One of :class:`pykechain.enums.ActivityClassification`
    :type classification: basestring
    :ivar activity_type: Type of the activity. One of :class:`pykechain.enums.ActivityType` for WIM version 2
    :type activity_type: basestring
    """

    def __init__(self, json, **kwargs):
        """Construct an Activity from a json object."""
        super(Activity2, self).__init__(json, **kwargs)

        self._scope_id = json.get('scope_id')

        self.ref = json.get('ref')
        self.description = json.get('description', '')
        self.status = json.get('status')
        self.classification = json.get('classification')  # type: ActivityClassification
        self.activity_type = json.get('activity_type')  # type: ActivityType
        self.start_date = parse_datetime(json.get('start_date'))
        self.due_date = parse_datetime(json.get('due_date'))

        self._tags = json.get('tags')

    def refresh(self, *args, **kwargs):
        """Refresh the object in place."""
        super(Activity2, self).refresh(url=self._client._build_url('activity', activity_id=self.id),
                                       extra_params=API_EXTRA_PARAMS['activity'])

    #
    # additional properties
    #

    @property
    def assignees(self) -> Optional[List['User']]:
        """List of assignees to the activity.

        Provides a list of `User` objects or an empty list. If no `assignees_ids` are in the API call, then
        returns None.

        :return: a list of `User`'s or an empty list.
        :rtype: list or None
        """
        if 'assignees_ids' in self._json_data and self._json_data.get('assignees_ids') == list():
            return []
        elif 'assignees_ids' in self._json_data and self._json_data.get('assignees_ids'):
            assignees_ids_str = ','.join([str(id) for id in self._json_data.get('assignees_ids')])
            return self._client.users(id__in=assignees_ids_str, is_hidden=False)
        return None

    @property
    def scope_id(self):
        """
        Id of the scope this Activity belongs to.

        This property will always produce a scope_id, even when the scope object was not included in an earlier
        response.

        When the :class:`Scope` is not included in this task, it will make an additional call to the KE-chain API.

        :return: the scope id
        :type: uuid
        :raises NotFoundError: if the scope could not be found
        """
        if self._scope_id is None:
            self.refresh()
            if self._scope_id is None:
                raise NotFoundError("This activity '{}'({}) does not belong to a scope, something is weird!".
                                    format(self.name, self.id))
        return self._scope_id

    @property
    def scope(self):
        """
        Scope this Activity belongs to.

        This property will return a `Scope` object. It will make an additional call to the KE-chain API.

        :return: the scope
        :type: :class:`pykechain.models.Scope`
        :raises NotFoundError: if the scope could not be found
        """
        return self._client.scope(pk=self.scope_id, status=None)

    #
    # predicates
    #

    def is_rootlevel(self):
        """
        Determine if the Activity is at the toplevel of a project, i.e. below the root itself.

        It will look for the name of the parent which should be either ActivityRootNames.WORKFLOW_ROOT or
        ActivityRootNames.CATALOG_ROOT. If the name of the parent cannot be found an additional API call is made
        to retrieve the parent object (based on the `parent_id` in the json_data).

        :return: Return True if it is a root level activity, otherwise return False
        :rtype: bool
        """
        # when the activity itself is a root, than return False immediately
        if self.is_root():
            return False

        parent_name = None
        parent_dict = self._json_data.get('parent_id_name')

        if parent_dict and 'name' in parent_dict:
            parent_name = parent_dict.get('name')
        if not parent_dict:
            parent_name = self._client.activity(id=self.parent_id).name

        return parent_name in ActivityRootNames.values()

    def is_task(self):
        """
        Determine if the Activity is of ActivityType.TASK.

        :return: Return True if it is a task, otherwise return False
        :rtype: bool
        """
        return self.activity_type == ActivityType.TASK

    def is_subprocess(self):
        """
        Determine if the Activity is of ActivityType.PROCESS.

        :return: Return True if it is a subprocess, otherwise return False
        :rtype: bool
        """
        return self.is_process()

    def is_process(self):
        """
        Determine if the Activity is of ActivityType.PROCESS.

        :return: Return True if it is a process, otherwise return False
        :rtype: bool
        """
        return self.activity_type == ActivityType.PROCESS

    def is_workflow(self):
        """
        Determine if the classification of the Activity is of ActivityClassification.WORKFLOW.

        :return: Return True if it is a workflow classification activity, otherwise return False
        :rtype: bool
        """
        return self.classification == ActivityClassification.WORKFLOW

    def is_catalog(self):
        """
        Determine if the classification of the Activity is of ActivityClassification.CATALOG.

        :return: Return True if it is a catalog classification activity, otherwise return False
        :rtype: bool
        """
        return self.classification == ActivityClassification.CATALOG

    def is_workflow_root(self):
        """
        Determine if the classification of the Activity is of ActivityClassification.WORKFLOW and a ROOT object.

        :return: Return True if it is a root workflow classification activity, otherwise return False
        :rtype: bool
        """
        return self.is_root() and self.is_workflow()

    def is_catalog_root(self):
        """
        Determine if the classification of the Activity is of ActivityClassification.CATALOG and a ROOT object.

        :return: Return True if it is a root catalog classification activity, otherwise return False
        :rtype: bool
        """
        return self.is_root() and self.is_catalog()

    def is_root(self):
        """
        Determine if the Activity is a ROOT object.

        If you want to determine if it is also a workflow or a catalog root, use :func:`Activity.is_workflow_root()`
        or :func:`Activity.is_catalog_root()` methods.

        :return: Return True if it is a root object, otherwise return False
        :rtype: bool
        """
        return self.name in ActivityRootNames.values() and self.parent_id is None

    def is_configured(self):
        """
        Determine if the Activity is configured with input and output properties.

        Makes an additional lightweight call to the API to determine if any associated models are there.

        :return: Return True if it is configured, otherwise return False
        :rtype: bool
        """
        # check configured based on if we get at least 1 part back
        return bool(self.parts(category=Category.MODEL, limit=1))

    def is_customized(self):
        """
        Determine if the Activity is customized.

        In other words if it has a customization. Use can use the :func:`Activity.customization()` to retrieve
        the customization object and configure the task.

        :return: Return True if it is customized, otherwise return False
        :rtype: bool
        """
        return bool(self._json_data.get('customization', False))

    #
    # methods
    #

    def create(self, *args, **kwargs) -> 'Activity2':
        """Create a new activity belonging to this subprocess.

        See :func:`pykechain.Client.create_activity` for available parameters.

        :raises IllegalArgumentError: if the `Activity2` is not a `PROCESS`.
        :raises APIError: if an Error occurs.
        """
        if self.activity_type != ActivityType.PROCESS:
            raise IllegalArgumentError("One can only create a task under a subprocess.")
        return self._client.create_activity(self, *args, **kwargs)

    def subprocess(self) -> 'Activity2':
        """Retrieve the subprocess in which this activity is defined.

        .. warning::
            This method is deprecated for newer releases of KE-chain (version 2.9.0 and higher). Please
            use the :func:`Activity2.parent()` method.

        If this is a task on top level, it raises NotFounderror.

        :return: a subprocess :class:`Activity2`
        :raises NotFoundError: when it is a task in the top level of a project
        :raises APIError: when other error occurs

        """
        raise ('Subprocess function is outdated in KE-chain 2.9.0, use `Activity2.parent()` method', DeprecationWarning)
        # return self.parent()

    def parent(self) -> 'Activity2':
        """Retrieve the parent in which this activity is defined.

        If this is a task on top level, it raises NotFounderror.

        :return: a :class:`Activity2`
        :raises NotFoundError: when it is a task in the top level of a project
        :raises APIError: when other error occurs

        Example
        -------
        >>> task = project.activity('Subtask')
        >>> parent_of_task = task.parent()

        """
        if self.parent_id is None:
            raise NotFoundError("Cannot find subprocess for this task '{}', "
                                "as this task exist on top level.".format(self.name))
        return self._client.activity(pk=self.parent_id, scope=self.scope_id)

    def children(self, **kwargs) -> List['Activity2']:
        """Retrieve the direct activities of this subprocess.

        It returns a combination of Tasks (a.o. UserTasks) and Subprocesses on the direct descending level.
        Only when the activity is a Subprocess, otherwise it raises a NotFoundError

        :param kwargs: Additional search arguments, check :func:`pykechain.Client.activities` for additional info
        :return: a list of :class:`Activity2`
        :raises NotFoundError: when this task is not of type `ActivityType.PROCESS`

        Example
        -------
        >>> task = project.activity('Subprocess')
        >>> children = task.children()

        Example searching for children of a subprocess which contains a name (icontains searches case insensitive)

        >>> task = project.activity('Subprocess')
        >>> children = task.children(name__icontains='more work')

        """
        if self.activity_type != ActivityType.PROCESS:
            raise NotFoundError("Only subprocesses can have children, please choose a subprocess instead of a '{}' "
                                "(activity '{}')".format(self.activity_type, self.name))
        if not kwargs:
            if self._cached_children is None:
                self._cached_children = self._client.activities(parent_id=self.id, scope=self.scope_id, **kwargs)
            return self._cached_children
        else:
            return self._client.activities(parent_id=self.id, scope=self.scope_id, **kwargs)

    def child(self,
              name: Optional[Text] = None,
              pk: Optional[Text] = None,
              **kwargs) -> 'Activity2':
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

        activity_list = list(self.children(name=name, pk=pk, **kwargs))

        criteria = '\nname: {}\npk: {}\nkwargs: {}'.format(name, pk, kwargs)

        if len(activity_list) == 1:
            child = activity_list[0]

        elif len(activity_list) > 1:
            raise MultipleFoundError('{} has more than one matching child.{}'.format(self, criteria))
        else:
            raise NotFoundError('{} has no matching child.{}'.format(self, criteria))
        return child

    def siblings(self, **kwargs) -> List['Activity2']:
        """Retrieve the other activities that also belong to the parent.

        It returns a combination of Tasks (a.o. UserTasks) and Subprocesses on the level of the current task, including
        itself. This also works if the activity is of type `ActivityType.PROCESS`.

        :param kwargs: Additional search arguments, check :func:`pykechain.Client.activities` for additional info
        :return: list of :class:`Activity2`
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
            raise NotFoundError("Cannot find subprocess for this task '{}', "
                                "as this task exist on top level.".format(self.name))
        return self._client.activities(parent_id=self.parent_id, scope=self.scope_id, **kwargs)

    def all_children(self) -> List['Activity2']:
        """
        Retrieve a flat list of all descendants, sorted depth-first.

        Returns an empty list for Activities of type TASK.

        :returns list of child objects
        :rtype List
        """
        if self.activity_type == ActivityType.TASK:
            return []
        return super().all_children()

    def edit_cascade_down(
        self,
        start_date: Optional[datetime.datetime] = None,
        due_date: Optional[datetime.datetime] = None,
        assignees: Optional[List[Text]] = None,
        assignees_ids: Optional[List[Text]] = None,
        status: Optional[Union[ActivityStatus, Text]] = None,
        overwrite: Optional[bool] = False,
    ) -> None:
        """
        Edit the activity and all its descendants with a single operation.

        :param start_date: (optionally) edit the start date of the activity as a datetime object (UTC time/timezone
                            aware preferred)
        :type start_date: datetime or None
        :param due_date: (optionally) edit the due_date of the activity as a datetime object (UTC time/timzeone
                            aware preferred)
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
        :rtype list[Activity2]
        """
        update_dict = {'id': self.id}

        self._validate_edit_arguments(
            update_dict=update_dict,
            start_date=start_date,
            due_date=due_date,
            assignees=assignees,
            assignees_ids=assignees_ids,
            status=status,
        )

        all_tasks = [self] + self.all_children()

        # Create update-json
        data = list()
        for task in all_tasks:
            task_specific_update_dict = dict(update_dict)

            if not overwrite:
                # Append the existing assignees of the task to the new assignees
                existing_assignees = [u.id for u in task.assignees]
                new_assignees = task_specific_update_dict.get('assignees_ids', list())
                task_specific_update_dict['assignees_ids'] = list(set(existing_assignees + new_assignees))

            task_specific_update_dict.update({'id': task.id})
            data.append(task_specific_update_dict)

        # Perform bulk update
        url = urljoin(self._client.api_root, 'api/activities/bulk_update')
        response = self._client._request('PUT', url, json=data)
        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update Activity ({})".format(response))

        # # Initialize all tasks with response
        # for task, response_json in zip(all_tasks, response.json().get('results')):
        #     task.__init__(client=self._client, json=response_json)
        #     if task == self:
        #         self.__init__(client=self._client, json=response_json)

        # return all_tasks

    def edit(
            self,
            name: Optional[Text] = None,
            description: Optional[Text] = None,
            start_date: Optional[datetime.datetime] = None,
            due_date: Optional[datetime.datetime] = None,
            assignees: Optional[List[Text]] = None,
            assignees_ids: Optional[List[Text]] = None,
            status: Optional[Union[ActivityStatus, Text]] = None,
            tags: Optional[List[Text]] = None,
    ) -> None:
        """Edit the details of an activity.

        :param name: (optionally) edit the name of the activity
        :type name: basestring or None
        :param description: (optionally) edit the description of the activity
        :type description: basestring or None
        :param start_date: (optionally) edit the start date of the activity as a datetime object (UTC time/timezone
                            aware preferred)
        :type start_date: datetime or None
        :param due_date: (optionally) edit the due_date of the activity as a datetime object (UTC time/timzeone
                            aware preferred)
        :type due_date: datetime or None
        :param assignees: (optionally) edit the assignees (usernames) of the activity as a list, will overwrite all
                          assignees
        :type assignees: list(basestring) or None
        :param assignees_ids: (optionally) edit the assignees (user id's) of the activity as a list, will overwrite all
                             assignees
        :type assignees_ids: list(basestring) or None
        :param status: (optionally) edit the status of the activity as a string based
                       on :class:`~pykechain.enums.ActivityStatus`
        :type status: ActivityStatus or None
        :param tags: (optionally) replace the tags on an activity, which is a list of strings ["one","two","three"]
        :type tags: list of basestring or None

        :raises NotFoundError: if a `username` in the list of assignees is not in the list of scope members
        :raises IllegalArgumentError: if the type of the inputs is not correct
        :raises APIError: if another Error occurs
        :warns: UserWarning - When a naive datetime is provided. Defaults to UTC.

        Example
        -------
        >>> from datetime import datetime
        >>> my_task = project.activity('Specify the wheel diameter')
        >>> my_task.edit(name='Specify wheel diameter and circumference',
        ...              description='The diameter and circumference are specified in inches',
        ...              start_date=datetime.utcnow(),  # naive time is interpreted as UTC time
        ...              assignee='testuser')

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
        >>> my_task.edit(due_date=due_date_tzaware, start_date=start_date_tzaware)

        """
        update_dict = {'id': self.id}
        if name is not None:
            if isinstance(name, (str, text_type)):
                update_dict.update({'name': name})
                self.name = name
            else:
                raise IllegalArgumentError('Name should be a string')

        if description is not None:
            if isinstance(description, (str, text_type)):
                update_dict.update({'description': description})
                self.description = description
            else:
                raise IllegalArgumentError('Description should be a string')

        if tags is not None:
            if isinstance(tags, (list, tuple, set)):
                update_dict.update({'tags': tags})
            else:
                raise IllegalArgumentError('tags should be a an array (list, tuple, set) of strings')

        self._validate_edit_arguments(
            update_dict=update_dict,
            start_date=start_date,
            due_date=due_date,
            assignees=assignees,
            assignees_ids=assignees_ids,
            status=status,
        )

        url = self._client._build_url('activity', activity_id=self.id)

        response = self._client._request('PUT', url, json=update_dict)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update Activity ({})".format(response))

        self.refresh(json=response.json().get('results')[0])

    def _validate_edit_arguments(self, update_dict, start_date, due_date, assignees, assignees_ids, status):
        """Verify inputs provided in both the `edit` and `edit_cascade_down` methods."""
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

        if isinstance(assignees_ids, (list, tuple)) or isinstance(assignees, (list, tuple)):
            members = self.scope.members()

            if isinstance(assignees_ids, (list, tuple)):
                update_assignees_ids = [m.get('id') for m in members if m.get('id') in assignees_ids]
                if len(update_assignees_ids) != len(assignees_ids):
                    raise NotFoundError("All assignees should be a member of the project")
            elif isinstance(assignees, (list, tuple)):
                update_assignees_ids = [m.get('id') for m in members if m.get('username') in assignees]
                if len(update_assignees_ids) != len(assignees):
                    raise NotFoundError("All assignees should be a member of the project")
            else:
                raise IllegalArgumentError("Provide the usernames either as list of usernames of user id's")

            update_dict.update({'assignees_ids': update_assignees_ids})
        elif assignees_ids or assignees:
            raise IllegalArgumentError("If assignees_ids or assignees are provided, they should be a list or tuple")

        if status is not None:
            if isinstance(status, (str, text_type)) and status in ActivityStatus.values():
                update_dict.update({'status': status})
            else:
                raise IllegalArgumentError('Status should be a string and in the list of acceptable '
                                           'status strings: {}'.format(ActivityStatus.values()))

        return update_dict

    def delete(self) -> bool:
        """Delete this activity.

        :return: True when successful
        :raises APIError: when unable to delete the activity
        """
        response = self._client._request('DELETE', self._client._build_url('activity', activity_id=self.id))

        if response.status_code != requests.codes.no_content:
            raise APIError("Could not delete activity: {} with id {}".format(self.name, self.id))
        return True

    #
    # Searchers and retrievers
    #

    def parts(self, *args, **kwargs):
        """Retrieve parts belonging to this activity.

        Without any arguments it retrieves the Instances related to this task only.

        This call only returns the configured properties in an activity. So properties that are not configured
        are not in the returned parts.

        See :class:`pykechain.Client.parts` for additional available parameters.

        Example
        -------
        >>> task = project.activity('Specify Wheel Diameter')
        >>> parts = task.parts()

        To retrieve the models only.
        >>> parts = task.parts(category=Category.MODEL)

        """
        if self._client.match_app_version(label='widget', version='>=3.0.0'):
            widget_manager = self.widgets()
            associated_parts = list()
            for widget in widget_manager:
                associated_parts.extend(widget.parts(*args, **kwargs))
            return associated_parts
        else:
            return self._client.parts(*args, activity=self.id, **kwargs)

    def associated_parts(self, *args, **kwargs):
        """Retrieve models and instances belonging to this activity.

        This is a convenience method for the :func:`Activity.parts()` method, which is used to retrieve both the
        `Category.MODEL` as well as the `Category.INSTANCE` in a tuple.

        This call only returns the configured properties in an activity. So properties that are not configured
        are not in the returned parts.

        If you want to retrieve only the models associated to this task it is better to use:
            `task.parts(category=Category.MODEL)`.

        See :func:`pykechain.Client.parts` for additional available parameters.

        :returns: a tuple(models of :class:`PartSet`, instances of :class:`PartSet`)

        Example
        -------
        >>> task = project.activity('Specify Wheel Diameter')
        >>> all_models, all_instances = task.associated_parts()

        """
        if self._client.match_app_version(label='widget', version='>=3.0.0'):
            widget_manager = self.widgets()
            associated_models = list()
            associated_instances = list()
            for widget in widget_manager:
                associated_models.extend(widget.parts(category=Category.MODEL, *args, **kwargs))
                associated_instances.extend(widget.parts(category=Category.INSTANCE, *args, **kwargs))
            return (
                associated_models,
                associated_instances
            )
        else:
            return (
                self.parts(category=Category.MODEL, *args, **kwargs),
                self.parts(category=Category.INSTANCE, *args, **kwargs)
            )

    def associated_object_ids(self) -> List[Dict]:
        """Retrieve object ids associated to this activity.

        This represents a more in-depth retrieval of objects associated to the activity. Each element in the list
        represents a `Property` of `Category.INSTANCE`. Each element contains the following fields:

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

        url = self._client._build_url('associations')

        response = self._client._request('GET', url, params=request_params)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve associations on activity: {}".format(response.content))

        data = response.json()
        return data['results']

    #
    # Customizations
    #

    def widgets(self, **kwargs) -> 'WidgetsManager':
        """
        Widgets of the activity.

        Works with KE-chain version 3.

        :param kwargs: additional keyword arguments
        :return: A :class:`WidgetManager` list, containing the widgets
        :rtype: WidgetManager
        :raises NotFoundError: when the widgets could not be found
        :raises APIError: when the API does not support the widgets, or when the API gives an error.
        """
        widgets = self._client.widgets(activity=self.id, **kwargs)
        return WidgetsManager(widgets=widgets, activity=self, client=self._client)

    def customization(self):
        """
        Get a customization object representing the customization of the activity.

        .. versionadded:: 1.11

        :return: An instance of :class:`customization.ExtCustomization`

        Example
        -------
        >>> activity = project.activity(name='Customizable activity')
        >>> customization = activity.customization()
        >>> part_to_show = project.part(name='Bike')
        >>> customization.add_property_grid_widget(part_to_show,custom_title="My super bike")

        """
        from .customization import ExtCustomization
        if self._client.match_app_version(label='widget', version='>=3.0.0'):
            raise DeprecationWarning("Customizations are deprecated. We introduced the `Widget` concept in version 3.")

        # For now, we only allow customization in an Ext JS context
        return ExtCustomization(activity=self, client=self._client)

    def configure(self, inputs, outputs):
        """
        Configure activity input and output.

        You need to provide a list of input and output :class:`Property`. Does not work with lists of propery id's.

        :param inputs: iterable of input property models
        :type inputs: list(:class:`Property`)
        :param outputs: iterable of output property models
        :type outputs: list(:class:`Property`)
        :raises APIError: when unable to configure the activity
        """
        def _get_propertyset(proplist):
            """Make it into a unique list of properties to configure for either inputs or outputs."""
            from pykechain.models import Property
            propertyset = []
            for property in proplist:
                if isinstance(property, Property):
                    propertyset.append(property.id)
                elif is_uuid(property):
                    propertyset.append(property)
            return list(set(propertyset))

        url = self._client._build_url('activity', activity_id='{}/update_associations'.format(self.id))

        if not all([p._json_data.get('category') == Category.MODEL for p in inputs]) and \
                not all([p._json_data.get('category') == Category.MODEL for p in outputs]):
            raise IllegalArgumentError('All Properties need to be of category MODEL to configure a task')

        response = self._client._request('PUT', url, json={
            'inputs': _get_propertyset(inputs),
            'outputs': _get_propertyset(outputs)
        })

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not configure activity")

        self.refresh(json=response.json().get('results')[0])

    def download_as_pdf(self, target_dir=None, pdf_filename=None, paper_size=PaperSize.A4,
                        paper_orientation=PaperOrientation.PORTRAIT, include_appendices=False):
        """
        Retrieve the PDF of the Activity.

        .. versionadded:: 2.1

        :param target_dir: (optional) directory path name where the store the log.txt to.
        :type target_dir: basestring or None
        :param pdf_filename: (optional) log filename to write the log to, defaults to `log.txt`.
        :type pdf_filename: basestring or None
        :param paper_size: The size of the paper to which the PDF is downloaded:
                               - a4paper (default): A4 paper size
                               - a3paper: A3 paper size
                               - a2paper: A2 paper size
                               - a1paper: A1 paper size
                               - a0paper: A0 paper size
        :type paper_size: basestring (see :class:`enums.PaperSize`)
        :param paper_orientation: The orientation of the paper to which the PDF is downloaded:
                               - portrait (default): portrait orientation
                               - landscape: landscape orientation
        :type paper_size: basestring (see :class:`enums.PaperOrientation`)
        :param include_appendices: True if the PDF should contain appendices, False (default) if otherwise.
        :type include_appendices: bool
        :raises APIError: if the pdf file could not be found.
        :raises OSError: if the file could not be written.
        """
        if not pdf_filename:
            pdf_filename = self.name + '.pdf'
        if not pdf_filename.endswith('.pdf'):
            pdf_filename += '.pdf'

        full_path = os.path.join(target_dir or os.getcwd(), pdf_filename)

        request_params = {
            'papersize': paper_size,
            'orientation': paper_orientation,
            'appendices': include_appendices
        }

        url = self._client._build_url('activity_export', activity_id=self.id)
        response = self._client._request('GET', url, params=request_params)
        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not download PDF of activity '{}': '{}'".format(self.name, response.content))

        # If appendices are included, the request becomes asynchronous

        if include_appendices:
            data = response.json()

            # Download the pdf async
            url = urljoin(self._client.api_root, data['download_url'])

            count = 0

            while count <= ASYNC_TIMEOUT_LIMIT:
                response = self._client._request('GET', url=url)

                if response.status_code == requests.codes.ok:  # pragma: no cover
                    with open(full_path, 'wb') as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                    return

                count += ASYNC_REFRESH_INTERVAL
                time.sleep(ASYNC_REFRESH_INTERVAL)

            raise APIError("Could not download PDF of activity {} within the time-out limit of {} "
                           "seconds".format(self.name, ASYNC_TIMEOUT_LIMIT))

        with open(full_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)

    def move(self, parent, classification=None):
        """
        Move the `Activity` to a new parent.

        See :func:`pykechain.Client.move_activity` for available parameters.

        If you want to move an Activity from one classification to another, you need to provide the target
        classification. The classificaiton of the parent should match the one provided in the function. This is
        to ensure that you really want this to happen.

        :param parent: parent object to move activity to
        :type parent: Union[Activity2, Text]
        :param classification: (optional) classification of the target parent if you want to change the classification.
        :type classification: ActivityClassification or None
        :raises IllegalArgumentError: if the 'parent' activity_type is not :class:`enums.ActivityType.SUBPROCESS`
        :raises IllegalArgumentError: if the 'parent' type is not :class:`Activity2` or UUID
        :raises APIError: if an Error occurs.
        """
        return self._client.move_activity(self, parent, classification=classification)
