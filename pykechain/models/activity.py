import warnings

import requests
import datetime

from six import text_type
from typing import Any  # flake8: noqa

from pykechain.exceptions import APIError, NotFoundError
from pykechain.models.base import Base


class Activity(Base):
    """A virtual object representing a KE-chain activity."""

    def __init__(self, json, **kwargs):
        # type: (dict, **Any) -> None
        """Construct an Activity from a json object."""
        super(Activity, self).__init__(json, **kwargs)

        self.scope = json.get('scope')

    def parts(self, *args, **kwargs):
        """Retrieve parts belonging to this activity.

        See :class:`pykechain.Client.parts` for available parameters.
        """
        return self._client.parts(*args, activity=self.id, **kwargs)

    def configure(self, inputs, outputs):
        """Configure activity input and output.

        :param inputs: iterable of input property models
        :param outputs: iterable of output property models
        :raises: APIError
        """
        url = self._client._build_url('activity', activity_id=self.id)

        r = self._client._request('PUT', url, params={'select_action': 'update_associations'}, json={
            'inputs': [p.id for p in inputs],
            'outputs': [p.id for p in outputs]
        })

        if r.status_code != 200:  # pragma: no cover
            raise APIError("Could not configure activity")

    def delete(self):
        """Delete this activity."""
        r = self._client._request('DELETE', self._client._build_url('activity', activity_id=self.id))

        if r.status_code != 204:
            raise APIError("Could not delete activity: {} with id {}".format(self.name, self.id))

    def create_activity(self, *args, **kwargs):
        """Create a new activity belonging to this subprocess.

        See :class:`pykechain.Client.create_activity` for available parameters.
        """
        return self._client.create_activity(self.id, *args, **kwargs)

    def edit(self, name=None, description=None, start_date=None, due_date=None, assignee=None):
        """Edit the details of an activity.

        :param name: (optionally) edit the name of the activity
        :param description: (optionally) edit the description of the activity
        :param start_date: (optionally) edit the start date of the activity as a datetime object (UTC time preferred)
        :param due_date: (optionally) edit the due_date of the activity as a datetime object (UTC time/timzeone aware preferred)
        :param assignee: (optionally) edit the assignee of the activity as a string

        :return: None
        :raises: NotFoundError, TypeError, APIError

        Example
        -------

        >>> from datetime import datetime
        >>> specify_wheel_diameter = project.activity('Specify wheel diameter')
        >>> specify_wheel_diameter.edit(name='Specify wheel diameter and circumference',
        ...                             description='The diameter and circumference are specified in inches', 
        ...                             start_date=datetime.utcnow(),  # naive time is interpreted as UTC time
        ...                             assignee='testuser')
        
        If we want to provide timezone aware datetime objects we can use the 3rd party convenience library `pytz`.
        
        >>> import pytz
        >>> start_date_tzaware = datetime.now(pytz.utc)
        >>> due_date_tzaware = datetime(2019, 10, 27, 23, 59, 0, tzinfo=pytz.timezone('Europe/Amsterdam'))
        >>> specify_wheel_diameter.edit(due_date=due_date_tzaware, start_date=start_date_tzaware)
        
        """
        update_dict = {'id': self.id}
        if name:
            if isinstance(name, (str, text_type)):
                update_dict.update({'name': name})
                self.name = name
            else:
                raise TypeError('Name should be a string')

        if description:
            if isinstance(description, (str, text_type)):
                update_dict.update({'description': description})
                self.description = description
            else:
                raise TypeError('Description should be a string')

        if start_date:
            if isinstance(start_date, datetime.datetime):
                if not start_date.tzinfo:
                    warnings.warn("The startdate '{}' is naive and not timezone aware, use tzinfo. "
                                  "This date is interpreted as UTC time.".format(start_date.isoformat(sep=' ')))
                update_dict.update({'start_date': start_date.isoformat(sep='T')})
                self.start_date = str(start_date)
            else:
                raise TypeError('Start date should be a datetime.datetime() object')

        if due_date:
            if isinstance(due_date, datetime.datetime):
                if not due_date.tzinfo:
                    warnings.warn("The duedate '{}' is naive and not timezone aware, use tzinfo. "
                                  "This date is interpreted as UTC time.".format(start_date.isoformat(sep=' ')))
                update_dict.update({'due_date': due_date.isoformat(sep='T')})
                self.due_date = str(due_date)
            else:
                raise TypeError('Due date should be a datetime.datetime() object')

        if assignee:
            if isinstance(assignee, (str, text_type)):
                project = self._client.scope(self._json_data['scope']['name'])
                members_list = [member['username'] for member in project._json_data['members']]
                if assignee in members_list:
                    update_dict.update({'assignee': assignee})
                    self.assignee = assignee
                else:
                    raise NotFoundError('Assignee should be a member of the scope')
            else:
                raise TypeError('Assignee should be a string')

        url = self._client._build_url('activity', activity_id=self.id)
        r = self._client._request('PUT', url, json=update_dict)

        if r.status_code != requests.codes.ok:
            raise APIError("Could not update Activity ({})".format(r))
