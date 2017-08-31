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

    # 1.11+
    def test_retrieve_scope_members(self):
        scope_managers = ['pykechain', 'testmanager', 'jochem.berends']
        scope_members = scope_managers + ['testuser']

        members_usernames = [member['username'] for member in self.project.members()]
        managers_usernames = [manager['username'] for manager in self.project.members(is_manager=True)]

        self.assertListEqual(sorted(scope_members), sorted(members_usernames))
        self.assertListEqual(sorted(scope_managers), sorted(managers_usernames))
