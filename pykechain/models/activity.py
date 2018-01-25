import datetime
import json
from typing import Any  # flake8: noqa

import requests
import warnings
from six import text_type

from pykechain.enums import Category, ActivityType
from pykechain.exceptions import APIError, NotFoundError, IllegalArgumentError
from pykechain.models.base import Base
from pykechain.models.inspector_base import Customization, InspectorComponent


class Activity(Base):
    """A virtual object representing a KE-chain activity."""

    def __init__(self, json, **kwargs):
        # type: (dict, **Any) -> None
        """Construct an Activity from a json object."""
        super(Activity, self).__init__(json, **kwargs)

        self.scope = json.get('scope', None)
        self.activity_type = json.get('activity_class', None)
        self.status = json.get('status', None)

    @property
    def scope_id(self):
        """
        ID of the scope this Activity belongs to.

        This property will always produce a scope_id, even when the scope object was not included in an earlier
        response.

        When the :class:`Scope` is not included in this task, it will make an additional call to the KE-chain API.

        :return: the scope id (uuid string)
        :raises NotFoundError: if the scope could not be found
        """
        if self.scope:
            scope_id = self.scope and self.scope.get('id')
        else:
            pseudo_self = self._client.activity(pk=self.id, fields="id,scope")
            if pseudo_self.scope and pseudo_self.scope.get('id'):
                self.scope = pseudo_self.scope
                scope_id = self.scope.get('id')
            else:
                raise NotFoundError("This activity '{}'({}) does not belong to a scope, something is weird!".
                                    format(self.name, self.id))
        return scope_id

    def parts(self, *args, **kwargs):
        """Retrieve parts belonging to this activity.

        Without any arguments it retrieves the Instances related to this task only.

        See :class:`pykechain.Client.parts` for additional available parameters.

        Example
        -------
        >>> task = project.activity('Specify Wheel Diameter')
        >>> parts = task.parts()

        To retrieve the models only.
        >>> parts = task.parts(category=Category.MODEL)

        """
        return self._client.parts(*args, activity=self.id, **kwargs)

    def associated_parts(self, *args, **kwargs):
        """Retrieve models and instances belonging to this activity.

        This is a convenience method for the :func:`Activity.parts()` method, which is used to retrieve both the
        `Category.MODEL` as well as the `Category.INSTANCE` in a tuple.

        If you want to retrieve only the models associated to this task it is better to use:
            `task.parts(category=Category.MODEL)`.

        See :func:`pykechain.Client.parts` for additional available parameters.

        :returns: a tuple(models of :class:`PartSet`, instances of :class:`PartSet`)

        Example
        -------
        >>> task = project.activity('Specify Wheel Diameter')
        >>> all_models, all_instances = task.associated_parts()

        """
        return self.parts(category=Category.MODEL, *args, **kwargs), \
               self.parts(category=Category.INSTANCE, *args, **kwargs)

    def configure(self, inputs, outputs):
        """Configure activity input and output.

        You need to provide a list of input and output :class:`Property`. Does not work with lists of propery id's.

        :param inputs: iterable of input property models
        :type inputs: list(:class:`Property`)
        :param outputs: iterable of output property models
        :type outputs: list(:class:`Property`)
        :raises APIError: when unable to configure the activity
        """
        url = self._client._build_url('activity', activity_id=self.id)

        r = self._client._request('PUT', url, params={'select_action': 'update_associations'}, json={
            'inputs': [p.id for p in inputs],
            'outputs': [p.id for p in outputs]
        })

        if r.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not configure activity")

    def delete(self):
        """Delete this activity.

        :raises APIError: when unable to delete the activity
        """
        r = self._client._request('DELETE', self._client._build_url('activity', activity_id=self.id))

        if r.status_code != requests.codes.no_content:
            raise APIError("Could not delete activity: {} with id {}".format(self.name, self.id))

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
        subprocess_id = self._json_data.get('container')
        if subprocess_id == self._json_data.get('root_container'):
            raise NotFoundError("Cannot find subprocess for this task '{}', "
                                "as this task exist on top level.".format(self.name))
        return self._client.activity(pk=subprocess_id, scope=self.scope_id)

    def children(self, **kwargs):
        """Retrieve the direct activities of this subprocess.

        It returns a combination of Tasks (a.o. UserTasks) and Subprocesses on the direct descending level.
        Only when the activity is a Subprocess, otherwise it raises a NotFoundError

        :param kwargs: Additional search arguments, check :func:`pykechain.Client.activities` for additional info
        :type kwargs: dict or None
        :return: a list of :class:`Activity`
        :raises NotFoundError: when this task is not of type `ActivityType.SUBPROCESS`

        Example
        -------
        >>> subprocess = project.subprocess('Subprocess')
        >>> children = subprocess.children()

        Example searching for children of a subprocess which contains a name (icontains searches case insensitive

        >>> subprocess = project.subprocess('Subprocess')
        >>> children = subprocess.children(name__icontains='more work')

        """
        if self.activity_type != ActivityType.SUBPROCESS:
            raise NotFoundError("Only subprocesses can have children, please choose a subprocess instead of a '{}' "
                                "(activity '{}')".format(self.activity_type, self.name))

        return self._client.activities(container=self.id, scope=self.scope_id, **kwargs)

    def siblings(self, **kwargs):
        """Retrieve the other activities that also belong to the subprocess.

        It returns a combination of Tasks (a.o. UserTasks) and Subprocesses on the level of the current task.
        This also works if the activity is of type `ActivityType.SUBPROCESS`.

        :param kwargs: Additional search arguments, check :func:`pykechain.Client.activities` for additional info
        :type kwargs: dict or None
        :return: list of :class:`Activity`

        Example
        -------
        >>> task = project.activity('Some Task')
        >>> siblings = task.siblings()

        Example for siblings containing certain words in the task name
        >>> task = project.activity('Some Task')
        >>> siblings = task.siblings(name__contains='Another Task')

        """
        container_id = self._json_data.get('container')
        return self._client.activities(container=container_id, scope=self.scope_id, **kwargs)

    def create(self, *args, **kwargs):
        """Create a new activity belonging to this subprocess.

        See :func:`pykechain.Client.create_activity` for available parameters.

        :raises IllegalArgumentError: if the `Activity` is not a `SUBPROCESS`.
        :raises APIError: if an Error occurs.
        """
        if self.activity_type != ActivityType.SUBPROCESS:
            raise IllegalArgumentError("One can only create a task under a subprocess.")
        return self._client.create_activity(self.id, *args, **kwargs)

    def edit(self, name=None, description=None, start_date=None, due_date=None, assignees=None, status=None):
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
        :param assignees: (optionally) edit the assignees of the activity as a list, will overwrite all assignees
        :type assignees: list(basestring) or None
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
        update_dict = {'id': self.id}
        if name:
            if isinstance(name, (str, text_type)):
                update_dict.update({'name': name})
                self.name = name
            else:
                raise IllegalArgumentError('Name should be a string')

        if description:
            if isinstance(description, (str, text_type)):
                update_dict.update({'description': description})
                self.description = description
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

        if assignees:
            if isinstance(assignees, list):
                project = self._client.scope(pk=self.scope_id, status=None)
                members_list = [member['username'] for member in project._json_data['members']]
                for assignee in assignees:
                    if assignee not in members_list:
                        raise NotFoundError("Assignee '{}' should be a member of the scope".format(assignee))
                update_dict.update({'assignees': assignees})
            else:
                raise IllegalArgumentError('Assignees should be a list')

        if status:
            if isinstance(status, (str, text_type)):
                update_dict.update({'status': status})
            else:
                raise IllegalArgumentError('Status should be a string')

        url = self._client._build_url('activity', activity_id=self.id)
        r = self._client._request('PUT', url, json=update_dict)

        if r.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update Activity ({})".format(r))

        if status:
            self._json_data['status'] = str(status)
        if assignees:
            self._json_data['assignees'] = assignees
        if due_date:
            self._json_data['due_date'] = str(due_date)
        if start_date:
            self._json_data['start_date'] = str(start_date)

    def customize(self, config):  # pragma: no cover
        """Customize an activity.

        .. warning::

           The use of `InspectorComponents` and `Customization` object is deprecated in November 2017. For
           KE-chain releases later than 2.5, please use the `activity.customization()` method to retrieve the newer
           type customization.

        :param config: the `InspectorComponent` or raw inspector json (as python dict) to be used in customization
        :type config: dict
        :raises InspectorComponentError: if the customisation is provided incorrectly.
        :raises IllegalArgumentError: when the configuration is incorrectly provided
        :raises DeprecationError: When the configuration is provided in a deprecated format
        :raises APIError: When an Error occurs in the communication with KE-chain

        Example
        -------
        >>> my_activity = self.project.activity('Customizable activity')
        >>> my_activity.customize(config =
        ...                          {"components":
        ...                              [{"xtype": "superGrid",
        ...                                "filter":
        ...                                    {"parent": "e5106946-40f7-4b49-ae5e-421450857911",
        ...                                     "model": "edc8eba0-47c5-415d-8727-6d927543ee3b"
        ...                                    }
        ...                              }]
        ...                          }
        ...                      )

        """
        if isinstance(config, dict):
            deprecated_customizations = Customization(json=config)
            deprecated_customizations.validate()
        elif isinstance(config, (Customization, InspectorComponent)):
            raise DeprecationWarning("The definition of customization widgets has changed in KE-chain version 2.5. "
                                     "The use of Customization and InspectorComponents is deprecated in November 2017")
            # config.validate()
            # deprecated_customizations = config
        else:
            raise IllegalArgumentError("Need to provide either a dictionary or Customization as input, got: '{}'".
                                       format(type(config)))

        activity_widget_config = self._json_data.get('widget_config')
        # When an activity has been costumized at least once before, then its widget config already exists
        if activity_widget_config:
            widget_config_id = activity_widget_config['id']
            request_update_dict = {'id': widget_config_id, 'config': json.dumps(deprecated_customizations.as_dict(),
                                                                                indent=2)}
            url = self._client._build_url('widget_config', widget_config_id=widget_config_id)
            r = self._client._request('PUT', url, json=request_update_dict)
        # When an activity was not customized before, then there is no widget config and a new one must be created for
        # that activity
        else:
            r = self._client._request('POST', self._client._build_url('widgets_config'),
                                      data=dict(
                                          activity=self.id,
                                          config=json.dumps(deprecated_customizations.as_dict(), indent=2))
                                      )

        if r.status_code in (requests.codes.ok, requests.codes.created):
            self._json_data['widget_config'] = {'id': r.json()['results'][0].get('id'),
                                                'config': json.dumps(deprecated_customizations.as_dict(), indent=2)}

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
        >>> customization.add_property_grid_widget(part_to_show, custom_title="My super bike"))

        """
        from .customization import ExtCustomization

        # For now, we only allow customization in an Ext JS context
        return ExtCustomization(activity=self, client=self._client)
