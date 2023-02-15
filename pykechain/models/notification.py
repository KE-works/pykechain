from typing import Dict, List, Optional, Union

import requests

from pykechain.enums import NotificationChannels, NotificationEvent, NotificationStatus
from pykechain.exceptions import APIError, IllegalArgumentError
from pykechain.models import Base
from pykechain.models.input_checks import check_base, check_enum, check_text, check_user
from pykechain.utils import Empty, clean_empty_values, empty, is_valid_email


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

        self.message = json.get("message", "")
        self.subject: str = json.get("subject", "")
        self.status: str = json.get("status", "")
        self.event: str = json.get("event", "")
        self.channels: List = json.get("channels", list())
        self.recipient_user_ids: List = json.get("recipient_users", list())
        self.team_id: str = json.get("team", "")
        self.from_user_id: str = json.get("from_user", "")

        self._from_user: Optional["User"] = None
        self._recipient_users: Optional[List["User"]] = None
        self._team: Optional["Team"] = None

    def __repr__(self):  # pragma: no cover
        return f"<pyke Notification id {self.id[-8:]}>"

    def get_recipient_users(self) -> List["User"]:
        """Return the list of actual `User` objects based on recipient_users_ids."""
        if self._recipient_users is None:
            self._recipient_users = self._client.users(
                id__in=",".join([str(pk) for pk in self.recipient_user_ids])
            )
        return self._recipient_users

    def get_from_user(self) -> "User":
        """Return the actual `User` object based on the from_user_id."""
        if self._from_user is None and self.from_user_id:
            self._from_user = self._client.user(pk=self.from_user_id)
        return self._from_user

    def get_team(self) -> "Team":
        """Return the actual `Team` object based on the team_id."""
        if self._team is None and self.team_id:
            self._team = self._client.team(pk=self.team_id)
        return self._team

    def delete(self):
        """Delete the notification."""
        return self._client.delete_notification(notification=self)

    def edit(
        self,
        subject: Optional[Union[str, Empty]] = empty,
        message: Optional[Union[str, Empty]] = empty,
        status: Optional[Union[NotificationStatus, Empty]] = empty,
        recipients: Optional[Union[List[Union["User", str, int]], Empty]] = empty,
        team: Optional[Union["Team", str, Empty]] = empty,
        from_user: Optional[Union["User", str, Empty]] = empty,
        event: Optional[Union[NotificationEvent, Empty]] = empty,
        channel: Optional[Union[NotificationChannels, Empty]] = empty,
        **kwargs,
    ) -> None:
        """
        Update the current `Notification` attributes.

        Setting an input to None will clear out the value (only applicable to recipients and from_user).

        :param subject: (O) Header text of the notification. Cannot be cleared.
        :type subject: basestring or None or Empty
        :param message: (O) Content message of the notification. Cannot be cleared.
        :type message: basestring or None or Empty
        :param status: (O) life-cycle status of the notification, defaults to "DRAFT". Cannot be cleared.
        :type status: NotificationStatus
        :param recipients: (O) list of recipients, each being a User object, user ID or an email address.
        :type recipients: list or None or Empty
        :param team: (O) team object to which the notification is constrained
        :type team: Team object or Team UUID
        :param from_user: (O) Sender of the notification, either a User object or user ID. Defaults to script user.
        :type from_user: User or user ID or None or Empty
        :param event: (O) originating event of the notification. Cannot be cleared.
        :type event: NotificationEvent
        :param channel: (O) method used to send the notification, defaults to "EMAIL". Cannot be cleared.
        :type channel: NotificationChannels
        :param kwargs: (optional) keyword=value arguments
        :return: None
        :raises: APIError: when the `Notification` could not be updated

        Not mentioning an input parameter in the function will leave it unchanged. Setting a parameter as None will
        clear its value (where that is possible). The example below will clear the from_user, but leave everything
        else unchanged.

        >>> notification.edit(from_user=None)

        """
        from pykechain.models import Team, User

        recipient_users = list()
        recipient_emails = list()

        if recipients is not None:
            if isinstance(recipients, list) and all(
                isinstance(r, (str, int, User)) for r in recipients
            ):
                for recipient in recipients:
                    if is_valid_email(recipient):
                        recipient_emails.append(recipient)
                    else:
                        recipient_users.append(check_user(recipient, User, "recipient"))
            elif isinstance(recipients, Empty):
                recipient_emails = empty
                recipient_users = empty
            else:
                raise IllegalArgumentError(
                    "`recipients` must be a list of User objects, IDs or email addresses, "
                    '"{}" ({}) is not.'.format(recipients, type(recipients))
                )

        if isinstance(channel, Empty):
            channels = empty
        elif check_enum(channel, NotificationChannels, "channel"):
            channels = [channel]
        else:
            channels = list()

        update_dict = {
            "status": check_enum(status, NotificationStatus, "status") or self.status,
            "event": check_enum(event, NotificationEvent, "event") or self.event,
            "subject": check_text(subject, "subject") or self.subject,
            "message": check_text(message, "message") or self.message,
            "recipient_users": recipient_users,
            "recipient_emails": recipient_emails,
            "team": check_base(team, Team, "team"),
            "from_user": check_user(from_user, User, "from_user"),
            "channels": channels or self.channels,
        }

        if kwargs:
            update_dict.update(kwargs)

        update_dict = clean_empty_values(update_dict=update_dict)

        url = self._client._build_url("notification", notification_id=self.id)

        response = self._client._request("PUT", url, json=update_dict)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError(f"Could not update Notification {self}", response=response)

        self.refresh(json=response.json().get("results")[0])
