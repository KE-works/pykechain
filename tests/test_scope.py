from pykechain.exceptions import NotFoundError, MultipleFoundError
from tests.classes import TestBetamax


class TestScopes(TestBetamax):

    def test_retrieve_scopes(self):
        self.assertTrue(self.client.scopes())

    def test_retrieve_single_unknown(self):
        with self.assertRaises(NotFoundError):
            self.client.scope('123lladadwd')

    def test_retrieve_single_multiple(self):
        with self.assertRaises(MultipleFoundError):
            self.client.scope()

    # 1.11+
    def test_retrieve_scope_members(self):
        original_scope_members = [u.get('username') for u in self.project.members()]
        original_scope_managers = [u.get('username') for u in self.project.members(is_manager=True)]
        scope_managers = original_scope_managers + ['testmanager']
        scope_members = original_scope_members + ['anotheruser', 'testuser']

        self.project.add_manager('testmanager')
        self.project.add_member('anotheruser')
        self.project.add_member('testuser')

        self.project.refresh()

        members_usernames = [member['username'] for member in self.project.members()]
        managers_usernames = [manager['username'] for manager in self.project.members(is_manager=True)]

        self.assertSetEqual(set(scope_members), set(members_usernames))
        self.assertSetEqual(set(scope_managers), set(managers_usernames))

        # teardown
        self.project.remove_member('anotheruser')

    def test_add_member(self):
        member_to_be_added = 'anotheruser'
        # testing
        self.project.add_member(member_to_be_added)
        self.project = self.client.scope(pk=self.project.id)
        project_members = self.project.members()
        self.assertTrue(member_to_be_added in [member['username'] for member in project_members])
        # teardown
        self.project.remove_member(member_to_be_added)

    def test_add_member_by_id(self):
        member_id = 4
        with self.assertRaises(TypeError):
            self.project.add_member(member_id)

    def test_add_non_existing_member(self):
        member_to_be_added = 'Nobody'
        with self.assertRaises(NotFoundError):
            self.project.add_member(member_to_be_added)

    def test_remove_member(self):
        member_to_be_removed = 'anotheruser'
        # setUp
        self.project.add_member(member_to_be_removed)
        # testing
        self.project.remove_member(member_to_be_removed)
        self.project = self.client.scope(pk=self.project.id)
        project_members = self.project.members()
        self.assertTrue(member_to_be_removed not in [member['username'] for member in project_members])

    def test_add_manager(self):
        manager_to_be_added = 'anotheruser'
        # testing
        self.project.add_manager(manager_to_be_added)
        self.project = self.client.scope(pk=self.project.id)
        project_managers = self.project.members(is_manager=True)
        self.assertTrue(manager_to_be_added in [manager['username'] for manager in project_managers])
        # teardown
        self.project.remove_member(manager_to_be_added)

    def test_remove_manager(self):
        manager_to_be_removed = 'anotheruser'
        # setUp
        self.project.add_manager(manager_to_be_removed)
        # testing
        self.project.remove_manager(manager_to_be_removed)
        self.project = self.client.scope(pk=self.project.id)
        project_managers = self.project.members(is_manager=True)
        self.assertTrue(manager_to_be_removed not in [manager['username'] for manager in project_managers])
        project_managers = self.project.members(is_manager=False)
        self.assertTrue(manager_to_be_removed in [manager['username'] for manager in project_managers])
        # teardown
        self.project.remove_member(manager_to_be_removed)
