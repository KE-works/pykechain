import datetime

from pykechain.enums import ScopeStatus
from pykechain.exceptions import NotFoundError, MultipleFoundError, IllegalArgumentError
from pykechain.models import Team
from tests.classes import TestBetamax


class TestScopes(TestBetamax):

    def test_retrieve_scopes(self):
        self.assertTrue(self.client.scopes())

    def test_retrieve_scope_with_kwargs(self):
        retrieve_scopes_with_kwargs = self.client.scopes(name__startswith='Bike')
        self.assertTrue(retrieve_scopes_with_kwargs)
        self.assertEqual(len(retrieve_scopes_with_kwargs), 1)

    def test_retrieve_single_unknown(self):
        with self.assertRaises(NotFoundError):
            self.client.scope('123lladadwd')

    def test_retrieve_single_multiple(self):
        with self.assertRaises(MultipleFoundError):
            self.client.scope()

    # 1.11
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

    # 2.2.0+
    def test_edit_scope(self):
        # setUp
        new_scope_name = 'Pykechain testing (bike project)'
        old_scope_name = self.project.name
        new_scope_description = 'Project used to build a Bike. Part-time job is to also test Pykechain.'
        old_scope_description = 'Project used to test Pykechain and push it to the limits'
        new_start_date = datetime.datetime(2018, 12, 5, tzinfo=None)
        old_start_date = datetime.datetime(2017, 4, 12)
        new_due_date = datetime.datetime(2018, 12, 8, tzinfo=None)
        old_due_date = datetime.datetime(2018, 4, 1)
        old_status = ScopeStatus.ACTIVE

        self.project.edit(name=new_scope_name, description=new_scope_description, start_date=new_start_date,
                          due_date=new_due_date, status=ScopeStatus.CLOSED)

        # testing
        retrieved_project = self.client.scope(id=self.project.id, status=ScopeStatus.CLOSED)

        self.assertTrue(retrieved_project.name == new_scope_name)
        self.assertTrue(retrieved_project._json_data['text'] == new_scope_description)
        self.assertTrue(retrieved_project._json_data['start_date'] == '2018-12-05T00:00:00Z')
        self.assertTrue(retrieved_project._json_data['due_date'] == '2018-12-08T00:00:00Z')
        self.assertTrue(retrieved_project._json_data['status'] == ScopeStatus.CLOSED)

        with self.assertRaises(IllegalArgumentError):
            self.project.edit(name=True)

        with self.assertRaises(IllegalArgumentError):
            self.project.edit(description=new_start_date)

        with self.assertRaises(IllegalArgumentError):
            self.project.edit(start_date='Yes, man!')

        with self.assertRaises(IllegalArgumentError):
            self.project.edit(due_date='Wrong')

        with self.assertRaises(IllegalArgumentError):
            self.project.edit(status='DEACTIVATED')

        # tearDown
        self.project.edit(name=old_scope_name, description=old_scope_description, start_date=old_start_date,
                          due_date=old_due_date, status=old_status)

    # v2.3.3
    def test_edit_scope_team(self):
        """Test capabilities of changing team scope."""

        # setup
        team_url = self.project._client._build_url('teams')

        r = self.project._client._request('get', team_url, params=dict(name='KE-works Team'))
        team_kew_id = r.json().get('results')[0].get('id')  # no iffer as it should fail hard when not a respcode =ok

        r = self.project._client._request('get', team_url, params=dict(name='Team B'))
        team_b_id = r.json().get('results')[0].get('id')

        # save current team
        team_dict = self.project._json_data.get('team')
        saved_team_id = team_dict and team_dict.get('id')

        self.project.edit(team=team_b_id)
        self.assertEqual(self.project._json_data.get('team').get('id'), team_b_id)

        self.project.edit(team=team_kew_id)
        self.assertEqual(self.project._json_data.get('team').get('id'), team_kew_id)

        self.project.edit(team=saved_team_id)
        self.assertEqual(self.project._json_data.get('team').get('id'), saved_team_id)

    def test_team_property_of_scope(self):
        """Test for the property 'team' of a scope."""
        team = self.project.team
        self.assertIsInstance(team, Team)

    def test_scope_tags(self):
        """test to retrieve the tags for a scope"""
        # setup
        saved_tags = self.project.tags

        # test
        scope_tags = ['a', 'list', 'of-tags']
        self.project.edit(tags=scope_tags)
        self.assertListEqual(scope_tags, self.project.tags)

        # teardown
        self.project.edit(tags=saved_tags)

    def test_scope_tags_may_be_emptied(self):
        # setup
        saved_tags = self.project.tags

        # test
        self.project.edit(tags=[])
        self.assertListEqual(self.project.tags, [])

        # teardown
        self.project.edit(tags=saved_tags)

    def test_delete_scope(self):
        # setUp
        scope_name = 'Test deletion scope'
        new_scope = self.client.create_scope(name=scope_name)
        self.assertEqual(len(self.client.scopes(name=scope_name)), 1)
        new_scope.delete()

        # testing
        with self.assertRaises(NotFoundError):
            self.client.scope(name=scope_name)

    def test_clone_scope(self):
        # setUp
        scope_name = 'Test cloning scope'
        scope_description = 'Description of clone scope'
        scope_start_date = datetime.datetime(2019, 4, 12)
        scope_due_date = datetime.datetime(2020, 4, 12)
        scope_team = self.client.team(name='Team No.1')

        scope_to_be_cloned = self.client.scope(name='Bike Project (pykechain testing)')
        cloned_scope = scope_to_be_cloned.clone(name=scope_name,
                                                status=ScopeStatus.CLOSED,
                                                tags=['cloned_scope'],
                                                description=scope_description,
                                                start_date=scope_start_date,
                                                due_date=scope_due_date,
                                                team=scope_team
                                                )

        # testing
        self.assertEqual(cloned_scope.name, scope_name)
        self.assertIsInstance(cloned_scope.team, Team)
        self.assertEqual(cloned_scope.team.name, 'Team No.1')
        self.assertEqual(cloned_scope.status, ScopeStatus.CLOSED)
        self.assertEqual(cloned_scope._json_data['text'], scope_description)
        self.assertEqual(cloned_scope._json_data['start_date'], scope_start_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
        self.assertEqual(cloned_scope._json_data['due_date'], scope_due_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
        self.assertIn('cloned_scope', cloned_scope.tags)

        # tearDown
        cloned_scope.delete()
