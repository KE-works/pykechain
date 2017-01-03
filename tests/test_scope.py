from pykechain.exceptions import NotFoundError, MultipleFoundError
from tests.classes import TestBetamax


class TestScopes(TestBetamax):

    def test_retrieve_scopes(self):
        assert self.client.scopes()

    def test_retrieve_single_unknown(self):
        with self.assertRaises(NotFoundError):
            self.client.scope('123lladadwd')

    def test_retrieve_single_multiple(self):
        with self.assertRaises(MultipleFoundError):
            self.client.scope()
