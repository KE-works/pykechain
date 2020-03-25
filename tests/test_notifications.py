from pykechain.exceptions import NotFoundError, MultipleFoundError
from pykechain.models import User
from pykechain.models.notification import Notification
from tests.classes import TestBetamax


class TestNotifications(TestBetamax):
    def setUp(self):
        super(TestNotifications, self).setUp()

        self.subject = 'TEST_SUBJECT'
        self.message = 'TEST_MESSAGE'
        self.recipient_users = [1]
        self.testing_notification = self.client.create_notification(subject=self.subject, message=self.message,
                                                                    recipient_users=self.recipient_users)

    def tearDown(self):
        self.testing_notification.delete()
        super(TestNotifications, self).tearDown()

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
        retrieved_notification = self.client.notification(message=self.message, subject=self.subject)
        self.assertIsInstance(retrieved_notification, Notification)

    def test_retrieve_notification_raise_not_found(self):
        with self.assertRaises(NotFoundError):
            self.client.notification(message="Doesn't exist")

    def test_retrieve_notification_raise_multiple_found(self):
        # setUp
        clone_testing_notification = self.client.create_notification(subject=self.subject, message=self.message)

        # testing
        with self.assertRaises(MultipleFoundError):
            self.client.notification(message=self.message, subject=self.subject)

        # tearDown
        clone_testing_notification.delete()

    def test_create_notification(self):
        # setUp
        subject = "This is testing the creation"
        message = "Will it work?"
        notification_created = self.client.create_notification(subject=subject,
                                                               message=message)
        # testing
        self.assertIsInstance(notification_created, Notification)
        self.assertEqual(notification_created.subject, subject)
        self.assertEqual(notification_created.message, message)

        # tearDown
        self.client.delete_notification(notification=notification_created)

    def test_delete_notification_from_client(self):
        # setUp
        message = "Testing deletion of notification"
        subject = "Testing deletion"
        notification = self.client.create_notification(message=message, subject=subject)
        self.client.delete_notification(notification=notification)

        # testing
        with self.assertRaises(NotFoundError):
            self.client.notification(message=message, subject=subject)

    def test_delete_notification(self):
        # setUp
        message = "Testing deletion of notification"
        subject = "Testing deletion"
        notification = self.client.create_notification(message=message, subject=subject)
        notification.delete()

        # testing
        with self.assertRaises(NotFoundError):
            self.client.notification(message=message, subject=subject)

    def test_get_recipient_users(self):
        self.testing_notification.get_recipient_users()

        # testing
        self.assertIsInstance(self.testing_notification.recipient_users, list)
        self.assertIsInstance(self.testing_notification.recipient_users[0], User)
        self.assertTrue(self.testing_notification.recipient_users[0].username == 'superuser')

