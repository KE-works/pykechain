from pykechain.models import Base
from typing import Text, List, Optional, Dict


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
        super(Notification, self).__init__(json, **kwargs)

        self.message = json.get('message', '')
        self.subject = json.get('subject', '')  # type: Text
        self.status = json.get('status', '')  # type: Text
        self.event = json.get('event', '')  # type: Text
        self.channels = json.get('channels', '')  # type: List
        self.recipient_user_ids = json.get('recipient_users', '')  # type: List
        self.from_user_id = json.get('from_user', '')

        self._from_user = None  # type: Optional['User']
        self._recipient_users = None  # type: Optional[List['User']]

    def __repr__(self):  # pragma: no cover
        return "<pyke Notification id {}>".format(self.id[-8:])

    def get_recipient_users(self) -> List['User']:
        """Return the list of actual `User` objects based on recipient_users_ids."""
        if self._recipient_users is None:
            self._recipient_users = self._client.users(id__in=','.join([str(pk) for pk in self.recipient_user_ids]))
        return self._recipient_users

    def get_from_user(self) -> 'User':
        """Return the actual `User` object based on from_user_id."""
        if self._from_user is None:
            self._from_user = self._client.user(pk=self.from_user_id)
        return self._from_user

    def delete(self):
        """Delete the notification."""
        return self._client.delete_notification(notification=self)
