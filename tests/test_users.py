from pykechain.exceptions import NotFoundError, MultipleFoundError
from tests.classes import TestBetamax


class TestUsers(TestBetamax):

    def test_retrieve_users(self):
        self.assertTrue(self.client.users())

    def test_retrieve_single_unknown_user(self):
        with self.assertRaises(NotFoundError):
            self.client.user('123lladadwd')

    def test_retrieve_single_multiple_user_raises_error(self):
        with self.assertRaises(MultipleFoundError):
            self.client.user()

    def test_retrieve_single_user_with_known_id(self):
        self.assertTrue(self.client.user(id=1))

    def test_retrieve_single_user_with_known_username(self):
        self.assertTrue(self.client.user(username='testuser'))

    def test_retrieve_user_timezone(self):
        user_retrieved = self.client.user(username='testuser')
        timezone_retrieved = user_retrieved.timezone
        self.assertEqual(timezone_retrieved.zone, 'Atlantic/Cape_Verde')

    def test_retrieve_user_name(self):
        user_retrieved = self.client.user(username='testuser')
        name_retrieved = user_retrieved.name
        self.assertEqual(name_retrieved, 'User Test')

    def test_retrieve_user_email(self):
        user_retrieved = self.client.user(username='testuser')
        email_retrieved = user_retrieved.email
        self.assertEqual(email_retrieved, 'a@b.nl')

    def test_retrieve_user_language(self):
        user_retrieved = self.client.user(username='testuser')
        language_retrieved = user_retrieved.language
        self.assertEqual(language_retrieved, 'fr')
