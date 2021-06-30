from pykechain.enums import NotificationEvent, NotificationChannels, NotificationStatus
from pykechain.exceptions import NotFoundError, MultipleFoundError, APIError, IllegalArgumentError
from pykechain.models import User, Team
from pykechain.models.notification import Notification
from tests.classes import TestBetamax


class _TestNotification(TestBetamax):
    SUBJECT = '_TEST_SUBJECT'
    MESSAGE = '_TEST_MESSAGE'
    USER_ID = 1

    def setUp(self) -> None:
        super().setUp()
        self.USER = self.client.user(pk=self.USER_ID)
        self.TEAM = self.client.teams()[0]

        for old_notification in self.client.notifications(subject=self.SUBJECT):
            old_notification.delete()


class TestNotificationCreation(_TestNotification):

    def setUp(self):
        super().setUp()
        self.bucket = list()

    def tearDown(self):
        for obj in self.bucket:
            try:
                obj.delete()
            except APIError:
                pass
        super().tearDown()

    def test_create(self):
        # setUp
        notification = self.client.create_notification(subject=self.SUBJECT,
                                                       message=self.MESSAGE)
        self.bucket.append(notification)

        # testing
        self.assertIsInstance(notification, Notification)
        self.assertEqual(self.SUBJECT, notification.subject)
        self.assertEqual(self.MESSAGE, notification.message)

    def test_create_with_inputs(self):
        notification = self.client.create_notification(
            subject=self.SUBJECT,
            message=self.MESSAGE,
            status=NotificationStatus.READY,
            recipients=[self.USER_ID],
            team=self.TEAM,
            from_user=self.USER_ID,
            event=NotificationEvent.EXPORT_ACTIVITY_ASYNC,
            channel=NotificationChannels.EMAIL,
        )
        self.bucket.append(notification)

        self.assertIsInstance(notification, Notification)
        self.assertEqual(NotificationStatus.READY, notification.status)
        self.assertEqual(self.USER_ID, notification.recipient_user_ids[0])
        self.assertEqual(self.TEAM, notification.get_team())
        self.assertEqual(self.USER, notification.get_from_user())
        self.assertEqual(NotificationEvent.EXPORT_ACTIVITY_ASYNC, notification.event)
        self.assertEqual(NotificationChannels.EMAIL, notification.channels[0])

    def test_create_invalid_inputs(self):
        kwargs = dict(subject=self.SUBJECT, message=self.MESSAGE)
        with self.assertRaises(IllegalArgumentError):
            self.bucket.append(self.client.create_notification(subject=False, message=self.MESSAGE))
        with self.assertRaises(IllegalArgumentError):
            self.bucket.append(self.client.create_notification(subject=self.SUBJECT, message=[self.MESSAGE]))
        with self.assertRaises(IllegalArgumentError):
            self.bucket.append(self.client.create_notification(status='sending', **kwargs))
        with self.assertRaises(IllegalArgumentError):
            self.bucket.append(self.client.create_notification(recipients='not a list', **kwargs))
        with self.assertRaises(IllegalArgumentError):
            self.bucket.append(self.client.create_notification(recipients=['not a user id'], **kwargs))
        with self.assertRaises(IllegalArgumentError):
            self.bucket.append(self.client.create_notification(team=0, **kwargs))
        with self.assertRaises(IllegalArgumentError):
            self.bucket.append(self.client.create_notification(from_user='Myself', **kwargs))
        with self.assertRaises(IllegalArgumentError):
            self.bucket.append(self.client.create_notification(event='Update', **kwargs))
        with self.assertRaises(IllegalArgumentError):
            self.bucket.append(self.client.create_notification(channel=[NotificationChannels.EMAIL], **kwargs))

    def test_delete_notification_from_client(self):
        # setUp
        notification = self.client.create_notification(message=self.MESSAGE, subject=self.SUBJECT)
        self.client.delete_notification(notification=notification)

        # testing
        with self.assertRaises(NotFoundError):
            self.client.notification(message=self.MESSAGE, subject=self.SUBJECT)

    def test_delete_notification(self):
        # setUp
        notification = self.client.create_notification(message=self.MESSAGE, subject=self.SUBJECT)
        notification.delete()

        # testing
        with self.assertRaises(NotFoundError):
            self.client.notification(message=self.MESSAGE, subject=self.SUBJECT)


class TestNotifications(_TestNotification):
    def setUp(self):
        super().setUp()
        self.notification = self.client.create_notification(
            subject=self.SUBJECT,
            message=self.MESSAGE,
            recipients=[self.USER_ID],
            team=self.TEAM,
        )

    def tearDown(self):
        self.notification.delete()
        super().tearDown()

    def test_all_notifications_retrieval(self):
        # setUp
        notifications = self.client.notifications()
        number_of_notification = len(notifications)
        dummy_notification = self.client.create_notification(subject="Dummy subject", message="Dummy message")

        notifications_retrieved_again = self.client.notifications()

        # testing
        self.assertTrue(len(notifications_retrieved_again) == number_of_notification + 1)

        # tearDown
        self.client.delete_notification(notification=dummy_notification)

    def test_retrieve_notification(self):
        # testing
        retrieved_notification = self.client.notification(message=self.MESSAGE, subject=self.SUBJECT)

        self.assertIsInstance(retrieved_notification, Notification)
        self.assertEqual(self.notification, retrieved_notification)

    def test_retrieve_notification_raise_not_found(self):
        with self.assertRaises(NotFoundError):
            self.client.notification(message="Doesn't exist")

    def test_retrieve_notification_raise_multiple_found(self):
        # setUp
        clone_testing_notification = self.client.create_notification(subject=self.SUBJECT, message=self.MESSAGE)

        # testing
        with self.assertRaises(MultipleFoundError):
            self.client.notification(message=self.MESSAGE, subject=self.SUBJECT)

        # tearDown
        clone_testing_notification.delete()

    def test_get_recipient_users(self):
        recipients = self.notification.get_recipient_users()

        # testing
        self.assertIsInstance(recipients, list)
        self.assertTrue(recipients)

        first_recipient = recipients[0]

        self.assertIsInstance(first_recipient, User)
        self.assertEqual('superuser', first_recipient.username)

    def test_get_from_user(self):
        from_user = self.notification.get_from_user()

        self.assertTrue(from_user)
        self.assertIsInstance(from_user, User)
        self.assertEqual('pykechain_user', from_user.username)

    def test_get_team(self):
        team = self.notification.get_team()

        self.assertIsInstance(team, Team)
        self.assertEqual(self.TEAM, team)

    def test_edit(self):
        subject = 'NEW SUBJECT'
        message = 'NEW MESSAGE'
        status = NotificationStatus.ARCHIVED
        recipients = [4]
        from_user = 4
        event = NotificationEvent.EXPORT_ACTIVITY_ASYNC
        channel = NotificationChannels.APP

        self.notification.edit(subject=subject, message=message, status=status, recipients=recipients, team=self.TEAM,
                               from_user=from_user, event=event, channel=channel)

        self.assertEqual(subject, self.notification.subject)
        self.assertEqual(message, self.notification.message)
        self.assertEqual(status, self.notification.status)
        self.assertListEqual(recipients, self.notification.recipient_user_ids)
        self.assertEqual(self.TEAM.id, self.notification.team_id)
        self.assertEqual(from_user, self.notification.from_user_id)
        self.assertEqual(event, self.notification.event)
        self.assertEqual(channel, self.notification.channels[0])

    def test_edit_incorrect_inputs(self):
        with self.assertRaises(IllegalArgumentError):
            self.notification.edit(subject=['Not a string'])
        with self.assertRaises(IllegalArgumentError):
            self.notification.edit(message=False)
        with self.assertRaises(IllegalArgumentError):
            self.notification.edit(status='Deleting')
        with self.assertRaises(IllegalArgumentError):
            self.notification.edit(recipients=True)
        with self.assertRaises(IllegalArgumentError):
            self.notification.edit(recipients=['Not a user ID'])
        with self.assertRaises(IllegalArgumentError):
            self.notification.edit(team=5)
        with self.assertRaises(IllegalArgumentError):
            self.notification.edit(from_user='self')
        with self.assertRaises(IllegalArgumentError):
            self.notification.edit(from_user=5.3)
        with self.assertRaises(IllegalArgumentError):
            self.notification.edit(event='Update')
        with self.assertRaises(IllegalArgumentError):
            self.notification.edit(channel=[NotificationChannels.APP])

    # test added due to #847 - providing no inputs overwrites values
    def test_edit_notification_clear_values(self):
        # setup
        initial_subject = 'NEW SUBJECT'
        initial_message = 'NEW MESSAGE'
        initial_status = NotificationStatus.ARCHIVED
        initial_recipients = [4]
        initial_from_user = 4
        initial_event = NotificationEvent.EXPORT_ACTIVITY_ASYNC
        initial_channel = NotificationChannels.APP

        self.notification.edit(subject=initial_subject, message=initial_message, status=initial_status,
                               recipients=initial_recipients, team=self.TEAM, from_user=initial_from_user,
                               event=initial_event, channel=initial_channel)

        # Edit without mentioning values, everything should stay the same
        new_subject = "AWESOME SUBJECT NEW"

        self.notification.edit(subject=new_subject)

        # testing
        self.assertEqual(self.notification.subject, new_subject)
        self.assertEqual(self.notification.message, initial_message)
        self.assertEqual(self.notification.status, initial_status)
        self.assertEqual(self.notification.recipient_user_ids, initial_recipients)
        self.assertEqual(self.notification.from_user_id, initial_from_user)
        self.assertEqual(self.notification.event, initial_event)
        self.assertEqual(self.notification.channels, [initial_channel])

        # Edit with clearing the values, name and status cannot be cleared
        self.notification.edit(subject=None, message=None, status=None, recipients=None, team=None, from_user=None,
                               event=None, channel=None)

        self.assertEqual(self.notification.subject, new_subject)
        self.assertEqual(self.notification.message, initial_message)
        self.assertEqual(self.notification.status, initial_status)
        self.assertEqual(self.notification.recipient_user_ids, list())
        self.assertEqual(self.notification.from_user_id, None)
        self.assertEqual(self.notification.event, initial_event)
        self.assertEqual(self.notification.channels, [initial_channel])
