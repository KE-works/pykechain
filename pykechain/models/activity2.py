import warnings

from pykechain.enums import ActivityType
from pykechain.exceptions import NotFoundError, IllegalArgumentError
from pykechain.models import Base, Activity


class Activity2(Activity):
    """A virtual object representing a KE-chain activity.

    .. versionadded:: 2.0
    """

    def __init__(self, json, **kwargs):
        # type: (dict, **Any) -> None
        """Construct an Activity from a json object."""
        super(Activity2, self).__init__(json, **kwargs)

        self.scope = json.get('scope', None)
        self.status = json.get('status', None)
        self.classification = json.get('classification', None)
        self.activity_type = json.get('activity_type', None)

    def create(self, *args, **kwargs):
        """Create a new activity belonging to this subprocess.

        See :func:`pykechain.Client.create_activity` for available parameters.

        :raises IllegalArgumentError: if the `Activity` is not a `SUBPROCESS`.
        :raises APIError: if an Error occurs.
        """
        if self.activity_type != ActivityType.PROCESS:
            raise IllegalArgumentError("One can only create a task under a subprocess.")
        return self._client.create_activity(self.id, *args, **kwargs)

    def subprocess(self):
        """Retrieve the subprocess in which this activity is defined.

        If this is a task on top level, it raises NotFounderror.

        :return: a subprocess :class:`Activity`
        :raises NotFoundError: when it is a task in the top level of a project
        :raises APIError: when other error occurs

        Example
        -------
        >>> task = project.activity('Subtask')
        >>> subprocess = task.subprocess()

        """
        warnings.warn('Subprocess function is outdated in KE-chain 2.8, use parent')

    def parent(self):
        parent_id = self._json_data.get('parent_id')
        if parent_id== None:
            raise NotFoundError("Cannot find subprocess for this task '{}', "
                                "as this task exist on top level.".format(self.name))
        return self._client.activity(pk=parent_id, scope=self.scope_id)

    def children(self, **kwargs):
        """Retrieve the direct activities of this subprocess.

        It returns a combination of Tasks (a.o. UserTasks) and Subprocesses on the direct descending level.
        Only when the activity is a Subprocess, otherwise it raises a NotFoundError

        :param kwargs: Additional search arguments, check :func:`pykechain.Client.activities` for additional info
        :type kwargs: dict or None
        :return: a list of :class:`Activity2`
        :raises NotFoundError: when this task is not of type `ActivityType.SUBPROCESS`

        Example
        -------
        >>> subprocess = project.subprocess('Subprocess')
        >>> children = subprocess.children()

        Example searching for children of a subprocess which contains a name (icontains searches case insensitive

        >>> subprocess = project.subprocess('Subprocess')
        >>> children = subprocess.children(name__icontains='more work')

        """
        if self.activity_type != ActivityType.PROCESS:
            raise NotFoundError("Only subprocesses can have children, please choose a subprocess instead of a '{}' "
                                "(activity '{}')".format(self.activity_type, self.name))

        return self._client.activities(parent_id=self.id, scope=self.scope_id, **kwargs)


    def edit(self, name=None, description=None, start_date=None, due_date=None, assignee_ids=None, status=None):
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
        :param assignee_ids: (optionally) edit the assignees of the activity as a list, will overwrite all assignees
        :type assignees_ids: list(basestring) or None
        :param status: (optionally) edit the status of the activity as a string based
                       on :class:`~pykechain.enums.ActivityType`
        :type status: basestring or None

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
        super(Activity2, self).edit(name=name, description=description, start_date=start_date, due_date=due_date,
                                    assignees=assignee_ids, status=status)

    def customize(self, config):
        """Deprecated function of customize."""
        raise DeprecationWarning('This function is deprecated')

