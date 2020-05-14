import requests

from pykechain.enums import NotificationStatus, NotificationEvent, NotificationChannels
from pykechain.exceptions import IllegalArgumentError, APIError
from pykechain.models import Base
from typing import Text, List, Optional, Dict, Union

from pykechain.models.input_checks import check_text, check_enum, check_base, check_user
from pykechain.utils import is_valid_email


class Notification(Base):
    """A virtual object representing a KE-chain notification.

    :ivar id: UUID of the notification
    :type id: basestring
    :ivar subject: subject of the notification
    :type subject: basestring or None
    :ivar created_at: the datetime when the object was created if available (otherwise None)
    :type created_at: datetime or None
    :ivar updated_at: the datetime when the object was last updated if available (otherwise None)
    :type updated_at: datetime or None
    :ivar status: The status of the notification (see :class:`pykechain.enums.NotificationStatus`)
    :type status: basestring or None
    :ivar event: The event of the notification (see :class:`pykechain.enums.NotificationEvent`)
    :type event: basestring or None
    :ivar recipient_users: The list of ids of the users
    :type recipient_users: List[User ids]
    """

    def __init__(self, json: Dict, **kwargs) -> None:
        """Construct a notification from a KE-chain 2 json response.

        :param json: the json response to construct the :class:`Notification` from
        :type json: dict
        """
        super().__init__(json, **kwargs)

        self.message = json.get('message', '')
        self.subject = json.get('subject', '')  # type: Text
        self.status = json.get('status', '')  # type: Text
        self.event = json.get('event', '')  # type: Text
        self.channels = json.get('channels', list())  # type: List
        self.recipient_user_ids = json.get('recipient_users', list())  # type: List
        self.team_id = json.get('team', '')  # type: Text
        self.from_user_id = json.get('from_user', '')  # type: Text

        self._from_user = None  # type: Optional['User']
        self._recipient_users = None  # type: Optional[List['User']]
        self._team = None  # type: Optional['Team']

    def __repr__(self):  # pragma: no cover
        return "<pyke Notification id {}>".format(self.id[-8:])

    def get_recipient_users(self) -> List['User']:
        """Return the list of actual `User` objects based on recipient_users_ids."""
        if self._recipient_users is None:
            self._recipient_users = self._client.users(id__in=','.join([str(pk) for pk in self.recipient_user_ids]))
        return self._recipient_users

    def get_from_user(self) -> 'User':
        """Return the actual `User` object based on the from_user_id."""
        if self._from_user is None and self.from_user_id:
            self._from_user = self._client.user(pk=self.from_user_id)
        return self._from_user

    def get_team(self) -> 'Team':
        """Return the actual `Team` object based on the team_id."""
        if self._team is None and self.team_id:
            self._team = self._client.team(pk=self.team_id)
        return self._team

    def delete(self):
        """Delete the notification."""
        return self._client.delete_notification(notification=self)

    def edit(
            self,
            subject: Optional[Text] = None,
            message: Optional[Text] = None,
            status: Optional[NotificationStatus] = None,
            recipients: Optional[List[Union['User', Text, int]]] = None,
            team: Optional[Union['Team', Text]] = None,
            from_user: Optional[Union['User', Text]] = None,
            event: Optional[NotificationEvent] = None,
            channel: Optional[NotificationChannels] = None,
            **kwargs
    ) -> None:
        """
        Update the current `Notification` attributes.

        :param subject: (O) Header text of the notification
        :type subject: str
        :param message: (O) Content message of the notification
        :type message: str
        :param status: (O) life-cycle status of the notification, defaults to "DRAFT".
        :type status: NotificationStatus
        :param recipients: (O) list of recipients, each being a User object, user ID or an email address.
        :type recipients: list
        :param team: (O) team object to which the notification is constrained
        :type team: Team object or Team UUID
        :param from_user: (O) Sender of the notification, either a User object or user ID. Defaults to script user.
        :type from_user: User or user ID
        :param event: (O) originating event of the notification.
        :type event: NotificationEvent
        :param channel: (O) method used to send the notification, defaults to "EMAIL".
        :type channel: NotificationChannels
        :param kwargs: (optional) keyword=value arguments
        :return: None
        :raises: APIError: when the `Notification` could not be updated
        """
        from pykechain.models import Team, User

        recipient_users = list()
        recipient_emails = list()

        if recipients is not None:
            if isinstance(recipients, list) and all(isinstance(r, (str, int, User)) for r in recipients):
                for recipient in recipients:
                    if is_valid_email(recipient):
                        recipient_emails.append(recipient)
                    else:
                        recipient_users.append(check_user(recipient, User, 'recipient'))
            else:
                raise IllegalArgumentError('`recipients` must be a list of User objects, IDs or email addresses, '
                                           '"{}" ({}) is not.'.format(recipients, type(recipients)))

        update_dict = {
            'status': check_enum(status, NotificationStatus, 'status'),
            'event': check_enum(event, NotificationEvent, 'event'),
            'subject': check_text(subject, 'subject'),
            'message': check_text(message, 'message'),
            'recipient_users': recipient_users,
            'recipient_emails': recipient_emails,
            'team': check_base(team, Team, 'team'),
            'from_user': check_user(from_user, User, 'from_user'),
            'channels': [channel] if check_enum(channel, NotificationChannels, 'channel') else [],
        }

        if kwargs:
            update_dict.update(kwargs)

        url = self._client._build_url('notification', notification_id=self.id)

        response = self._client._request('PUT', url, json=update_dict)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update Notification {}".format(self), response=response)

        self.refresh(json=response.json().get('results')[0])
