from pykechain.enums import LanguageCodes
from pykechain.exceptions import NotFoundError, MultipleFoundError
from tests.classes import TestBetamax


class TestUsers(TestBetamax):

    def test_retrieve_users(self):
        self.assertTrue(self.client.users())

    def test_retrieve_single_unknown_user(self):
        with self.assertRaises(NotFoundError):
            self.client.user('123lladadwd')

    def test_user_attributes(self):
        attributes = ['_client', '_json_data', 'id', 'name', 'created_at', 'updated_at',
                      'username', 'timezone', 'language', 'email']

        obj = self.client.users()[0]
        for attribute in attributes:
            with self.subTest(msg=attribute):
                self.assertTrue(hasattr(obj, attribute),
                                "Could not find '{}' in the object: '{}'".format(attribute, obj.__dict__))

    def test_retrieve_single_multiple_user_raises_error(self):
        with self.assertRaises(MultipleFoundError):
            self.client.user()

    def test_retrieve_single_user_with_known_id(self):
        self.assertTrue(self.client.user(pk=1))

    def test_retrieve_single_user_with_known_username(self):
        self.assertTrue(self.client.user(username='testuser'))

    def test_retrieve_user_timezone(self):
        user_retrieved = self.client.user(username='testuser')
        timezone_retrieved = user_retrieved.timezone
        self.assertIn(timezone_retrieved.zone, ['Atlantic/Cape_Verde', 'UTC'])

    def test_retrieve_user_name(self):
        user_retrieved = self.client.user(username='testuser')
        name_retrieved = user_retrieved.name
        self.assertIn(name_retrieved, ['User Test', ''])

    def test_retrieve_default_name(self):
        user_retrieved = self.client.user(username='testuser')
        default_name = user_retrieved.default_name
        self.assertIsInstance(default_name, str)
        self.assertIn(default_name, user_retrieved.username)

    def test_retrieve_user_email(self):
        user_retrieved = self.client.user(username='testuser')
        email_retrieved = user_retrieved.email
        self.assertEqual('a@b.nl', email_retrieved)

    def test_retrieve_user_language(self):
        user_retrieved = self.client.user(username='testuser')
        language_retrieved = user_retrieved.language
        self.assertIn(language_retrieved, LanguageCodes.values())

    def test_now_in_my_timezone(self):
        user_retrieved = self.client.user(username="testuser")
        now = user_retrieved.now_in_my_timezone()
        import datetime
        self.assertIsInstance(now, datetime.datetime)
