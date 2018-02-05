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

    def test_retrieve_single_user_with_known_username(self):
        self.assertTrue(self.client.user(id=1))
