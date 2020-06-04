import datetime
import os
import time
from typing import List, Text, Dict, Optional, Union
from urllib.parse import urljoin

import requests

from pykechain.defaults import ASYNC_REFRESH_INTERVAL, ASYNC_TIMEOUT_LIMIT, API_EXTRA_PARAMS
from pykechain.enums import ActivityType, ActivityStatus, Category, ActivityClassification, ActivityRootNames, \
    PaperSize, PaperOrientation
from pykechain.exceptions import NotFoundError, IllegalArgumentError, APIError, MultipleFoundError
from pykechain.models.input_checks import check_datetime, check_text, check_list_of_text, check_enum, check_user, \
    check_type
from pykechain.models.representations.component import RepresentationsComponent
from pykechain.models.tags import TagsMixin
from pykechain.models.tree_traversal import TreeObject
from pykechain.models.user import User
from pykechain.models.widgets.widgets_manager import WidgetsManager
from pykechain.utils import parse_datetime, is_valid_email


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
        super().__init__(json, **kwargs)

        self._scope_id = json.get('scope_id')

        self.ref = json.get('ref')  # type: Text
        self.description = json.get('description', '')  # type: Text
        self.status = json.get('status')  # type: ActivityStatus
        self.classification = json.get('classification')  # type: ActivityClassification
        self.activity_type = json.get('activity_type')  # type: ActivityType
        self.start_date = parse_datetime(json.get('start_date'))
        self.due_date = parse_datetime(json.get('due_date'))
        self.assignees_ids = json.get('assignees_ids', [])  # type: List[Text]
        self._options = json.get('activity_options', {})

        self._tags = json.get('tags', [])  # type: List[Text]
        self._representations_container = RepresentationsComponent(
            self,
            self._options.get('representations', {}),
            self._save_representations,
        )

    def __call__(self, *args, **kwargs) -> 'Activity2':
        """Short-hand version of the `child` method."""
        return self.child(*args, **kwargs)

    def refresh(self, *args, **kwargs):
        """Refresh the object in place."""
        super().refresh(url=self._client._build_url('activity', activity_id=self.id),
                        extra_params=API_EXTRA_PARAMS['activity'], *args, **kwargs)

    #
    # additional properties
    #

    @property
    def assignees(self) -> List['User']:
        """List of assignees to the activity.

        Provides a list of `User` objects or an empty list.

        :return: a list of `User` objects or an empty list.
        :rtype: list
        """
        return self._client.users(id__in=self.assignees_ids, is_hidden=False) if self.assignees_ids else []

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
                raise NotFoundError("Activity '{}' has no related scope!".format(self))
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
        self._options.update({'representations': representation_options})
        self.edit(activity_options=self._options)

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
            raise NotFoundError("Cannot find parent for task '{}', as this task exist on top level.".format(self))
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
            raise NotFoundError("Cannot find siblings for task '{}', as this task exist on top level.".format(self))
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
            **kwargs
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
            **kwargs
        )

        all_tasks = [self] + self.all_children()
        new_assignees = update_dict.get('assignees_ids', list())

        # Create update-json
        data = list()
        for task in all_tasks:
            task_specific_update_dict = dict(update_dict)

            if not overwrite:
                # Append the existing assignees of the task to the new assignees
                existing_assignees = [u.id for u in task.assignees]
                task_specific_update_dict['assignees_ids'] = list(set(existing_assignees + new_assignees))

            task_specific_update_dict.update({'id': task.id})
            data.append(task_specific_update_dict)

        # Perform bulk update
        url = self._client._build_url('activities_bulk_update')
        response = self._client._request('PUT', url, json=data)
        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update Activity {}".format(self), response=response)

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
            **kwargs
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
        update_dict = {
            'id': self.id,
            'name': check_text(text=name, key='name') or self.name,
            'description': check_text(text=description, key='description') or self.description or '',
        }
        if tags is not None:
            update_dict['tags'] = check_list_of_text(tags, 'tags', True)

        self._validate_edit_arguments(
            update_dict=update_dict,
            start_date=start_date,
            due_date=due_date,
            assignees=assignees,
            assignees_ids=assignees_ids,
            status=status,
            **kwargs,
        )

        url = self._client._build_url('activity', activity_id=self.id)

        response = self._client._request('PUT', url, json=update_dict, params=API_EXTRA_PARAMS['activity'])

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update Activity {}".format(self), response=response)

        self.refresh(json=response.json().get('results')[0])

    def _validate_edit_arguments(self, update_dict, start_date, due_date, assignees, assignees_ids, status, **kwargs):
        """Verify inputs provided in both the `edit` and `edit_cascade_down` methods."""
        if assignees and assignees_ids:
            raise IllegalArgumentError('Provide either assignee names or their ids, but not both.')

        assignees = assignees if assignees is not None else assignees_ids

        if assignees:
            if not isinstance(assignees, (list, tuple, set)) or not all(isinstance(a, (str, int)) for a in assignees):
                raise IllegalArgumentError('All assignees must be provided as list, tuple or set of names or IDs.')

            update_assignees_ids = [m.get('id') for m in self.scope.members()
                                    if m.get('id') in assignees or m.get('username') in set(assignees)]

            if len(update_assignees_ids) != len(assignees):
                raise NotFoundError('All assignees should be a member of the project.')
        else:
            update_assignees_ids = []

        update_dict.update({
            'assignees_ids': update_assignees_ids,
            'start_date': check_datetime(dt=start_date, key='start_date'),
            'due_date': check_datetime(dt=due_date, key='due_date'),
            'status': check_enum(status, ActivityStatus, 'status') or self.status,
        })

        if kwargs:
            update_dict.update(kwargs)

        return update_dict

    def delete(self) -> bool:
        """Delete this activity.

        :return: True when successful
        :raises APIError: when unable to delete the activity
        """
        response = self._client._request('DELETE', self._client._build_url('activity', activity_id=self.id))

        if response.status_code != requests.codes.no_content:
            raise APIError("Could not delete Activity {}.".format(self), response=response)
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
        return [p for w in self.widgets() for p in w.parts(*args, **kwargs)]

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
        associated_models = list()
        associated_instances = list()
        for widget in self.widgets():
            associated_models.extend(widget.parts(category=Category.MODEL, *args, **kwargs))
            associated_instances.extend(widget.parts(category=Category.INSTANCE, *args, **kwargs))

        return (
            associated_models,
            associated_instances
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
            raise NotFoundError("Could not retrieve Associations on Activity {}".format(self), response=response)

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
            raise APIError("Could not download PDF of Activity {}".format(self), response=response)

        # If appendices are included, the request becomes asynchronous

        if include_appendices:  # pragma: no cover
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

            raise APIError("Could not download PDF of Activity {} within the time-out limit of {} "
                           "seconds".format(self, ASYNC_TIMEOUT_LIMIT), response=response)

        with open(full_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)

    def move(self, parent, classification=None):
        """
        Move the `Activity` to a new parent.

        See :func:`pykechain.Client.move_activity` for available parameters.

        If you want to move an Activity from one classification to another, you need to provide the target
        classification. The classification of the parent should match the one provided in the function. This is
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

    def share_link(self, subject: Text, message: Text, recipient_users: List[Union[User, Text]]) -> None:
        """
        Share the link of the `Activity` through email.

        :param subject: subject of email
        :type subject: basestring
        :param message: message of email
        :type message: basestring
        :param recipient_users: users that will receive the email
        :type recipient_users: list(Union(User, Id))
        :raises APIError: if an internal server error occurred.
        """
        params = dict(
            message=check_text(message, 'message'),
            subject=check_text(subject, 'subject'),
            recipient_users=[check_user(recipient, User, 'recipient') for recipient in recipient_users],
            activity_id=self.id
        )

        url = self._client._build_url('notification_share_activity_link')

        response = self._client._request('POST', url, data=params)

        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError("Could not share the link to Activity {}".format(self), response=response)

    def share_pdf(
            self,
            subject: Text,
            message: Text,
            recipient_users: List[Union[User, Text]],
            paper_size: Optional[PaperSize] = PaperSize.A3,
            paper_orientation: Optional[PaperOrientation] = PaperOrientation.PORTRAIT,
            include_appendices: Optional[bool] = False
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
        :param include_appendices: True if the PDF should contain appendices, False (default) if otherwise.
        :type include_appendices: bool
        :raises APIError: if an internal server error occurred.
        """
        recipient_emails = list()
        recipient_users_ids = list()
        if isinstance(recipient_users, list) and all(isinstance(r, (str, int, User)) for r in recipient_users):
            for user in recipient_users:
                if is_valid_email(user):
                    recipient_emails.append(user)
                else:
                    recipient_users_ids.append(check_user(user, User, 'recipient'))
        else:
            raise IllegalArgumentError('`recipients` must be a list of User objects, IDs or email addresses, '
                                       '"{}" ({}) is not.'.format(recipient_users, type(recipient_users)))

        params = dict(
            message=check_text(message, 'message'),
            subject=check_text(subject, 'subject'),
            recipient_users=recipient_users_ids,
            recipient_emails=recipient_emails,
            activity_id=self.id,
            papersize=check_enum(paper_size, PaperSize, 'paper_size'),
            orientation=check_enum(paper_orientation, PaperOrientation, 'paper_orientation'),
            appendices=check_type(include_appendices, bool, 'bool'),
        )

        url = self._client._build_url('notification_share_activity_pdf')

        response = self._client._request('POST', url, data=params)

        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError("Could not share the link to Activity {}".format(self), response=response)
