import datetime
from time import sleep
from unittest import skipIf

from pykechain.enums import ScopeStatus, KEChainPages
from pykechain.exceptions import NotFoundError, MultipleFoundError, IllegalArgumentError
from pykechain.models import Team, Scope2
from pykechain.models.sidebar.sidebar_manager import SideBarManager
from tests.classes import TestBetamax
from tests.utils import TEST_FLAG_IS_PIM3


class TestScopes(TestBetamax):

    def test_retrieve_scopes(self):
        self.assertTrue(self.client.scopes())

    def test_scope_attributes(self):
        attributes = ['_client', '_json_data', 'id', 'name', 'created_at', 'updated_at', 'ref',
                      'process', 'workflow_root', 'description', 'status', 'category', 'tags',
                      'start_date', 'due_date']

        obj = self.project
        for attribute in attributes:
            self.assertTrue(hasattr(obj, attribute),
                            "Could not find '{}' in the object: '{}'".format(attribute, obj.__dict__.keys()))

    def test_retrieve_scope_with_kwargs(self):
        retrieve_scopes_with_kwargs = self.client.scopes(name__icontains='Bike')
        self.assertTrue(retrieve_scopes_with_kwargs)
        self.assertTrue(len(retrieve_scopes_with_kwargs) >= 1)

    def test_retrieve_single_unknown(self):
        with self.assertRaises(NotFoundError):
            self.client.scope('123lladadwd')

    def test_retrieve_single_multiple(self):
        with self.assertRaises(MultipleFoundError):
            self.client.scope()

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

    def test_add_leadmember(self):
        leadmember_to_be_added = 'anotheruser'
        # testing
        self.project.add_leadmember(leadmember_to_be_added)
        self.project = self.client.scope(pk=self.project.id)
        project_leadmembers = self.project.members(is_leadmember=True)
        self.assertTrue(leadmember_to_be_added in [leadmember['username'] for leadmember in project_leadmembers])
        # teardown
        self.project.remove_member(leadmember_to_be_added)

    def test_remove_leadmember(self):
        leadmember_to_be_removed = 'anotheruser'
        # setUp
        self.project.add_leadmember(leadmember_to_be_removed)
        # testing
        self.project.remove_leadmember(leadmember_to_be_removed)
        self.project = self.client.scope(pk=self.project.id)
        project_leadmembers = self.project.members(is_leadmember=True)
        self.assertTrue(leadmember_to_be_removed not in [leadmember['username'] for leadmember in project_leadmembers])
        project_leadmembers = self.project.members(is_leadmember=False)
        self.assertTrue(leadmember_to_be_removed in [leadmember['username'] for leadmember in project_leadmembers])
        # teardown
        self.project.remove_member(leadmember_to_be_removed)

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
        self.assertTrue(retrieved_project._json_data['start_date'] in ('2018-12-05T00:00:00Z', '2018-12-05T00:00:00+00:00'))
        self.assertTrue(retrieved_project._json_data['due_date'] in ('2018-12-08T00:00:00Z', '2018-12-08T00:00:00+00:00'))
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
            self.project.edit(status='ILLEGAL_STATUS_WILL_CAUSE_ERR')

        # tearDown
        self.project.edit(name=old_scope_name, description=old_scope_description, start_date=old_start_date,
                          due_date=old_due_date, status=old_status)

    # v2.3.3
    def test_edit_scope_team(self):
        """Test capabilities of changing team scope."""

        # setup
        team_url = self.project._client._build_url('teams')

        r = self.project._client._request('get', team_url, params=dict(name='Team No.1'))
        team_kew_id = r.json().get('results')[0].get('id')  # no iffer as it should fail hard when not a respcode =ok

        r = self.project._client._request('get', team_url, params=dict(name='Second Team'))
        team_b_id = r.json().get('results')[0].get('id')

        # save current team
        if self.client.match_app_version(label="pim", version=">=3.0.0"):
            team_dict = self.project._json_data.get('team_id_name')
            saved_team_id = team_dict and team_dict.get('id')
        else:
            team_dict = self.project._json_data.get('team')
            saved_team_id = team_dict and team_dict.get('id')

        self.project.edit(team=team_b_id)
        if self.client.match_app_version(label="pim", version=">=3.0.0"):
            self.assertEqual(self.project._json_data.get('team_id_name').get('id'), team_b_id)
        else:
            self.assertEqual(self.project._json_data.get('team').get('id'), team_b_id)

        self.project.edit(team=team_kew_id)
        if self.client.match_app_version(label="pim", version=">=3.0.0"):
            self.assertEqual(self.project._json_data.get('team_id_name').get('id'), team_kew_id)
        else:
            self.assertEqual(self.project._json_data.get('team').get('id'), team_kew_id)

        self.project.edit(team=saved_team_id)
        if self.client.match_app_version(label="pim", version=">=3.0.0"):
            self.assertEqual(self.project._json_data.get('team_id_name').get('id'), saved_team_id)
        else:
            self.assertEqual(self.project._json_data.get('team').get('id'), saved_team_id)

    def test_team_property_of_scope(self):
        """Test for the property 'team' of a scope."""
        team = self.project.team
        self.assertIsInstance(team, Team)


@skipIf(not TEST_FLAG_IS_PIM3, reason="This tests is designed for PIM version 2, expected to fail on old PIM")
class TestScopes2SpecificTests(TestBetamax):

    def setUp(self):
        """
        SetUp the test.

        When you create a scope, assign it to self.scope such that it is deleted when the test is complete

        :ivar scope: scope that you create during a test, which will be autoremoved in the cleanup.
        """
        super(TestScopes2SpecificTests, self).setUp()
        self.scope = None

    def tearDown(self):
        """Teardown the test, remove the scope.

        When you create a scope, assign it to self.scope such that it is deleted when the test is complete
        """
        if self.scope:
            self.scope.delete()
        super(TestScopes2SpecificTests, self).tearDown()

    def test_side_bar(self):
        side_bar_manager = self.project.side_bar()

        self.assertIsInstance(side_bar_manager, SideBarManager)

    def test_set_landing_page_activity(self):
        self.scope = self.project.clone(asynchronous=False)

        first_activity = self.scope.activities()[0]

        self.scope.set_landing_page(activity=first_activity)

    def test_set_landing_page_data_model(self):
        self.scope = self.project.clone(asynchronous=False)

        data_model_page = KEChainPages.DATA_MODEL

        self.scope.set_landing_page(activity=data_model_page)

    def test_retrieve_scope2_members(self):
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

    def test_members(self):

        # Helper function:
        def get_member_names(**kwargs):
            return [member['username'] for member in self.project.members(**kwargs)]

        all_members = set(get_member_names())
        managers = set(get_member_names(is_manager=True))
        non_managers = set(get_member_names(is_manager=False))
        leads = set(get_member_names(is_leadmember=True))
        non_leads = set(get_member_names(is_leadmember=False))
        basic_members = set(get_member_names(is_manager=False, is_leadmember=False))
        lead_and_manager = set(get_member_names(is_manager=True, is_leadmember=True))

        self.assertTrue(len(all_members) == 4, msg='Number of default scope members has changed!')
        self.assertTrue(basic_members and leads and managers and lead_and_manager,
                        msg='Test scope must have a member of every type!')

        all_roles = basic_members | leads | managers | lead_and_manager
        remaining_non_leads = all_roles - leads
        remaining_non_managers = all_roles - managers

        self.assertSetEqual(all_roles, all_members, msg='The sum of all roles should equal all members.')
        self.assertSetEqual(remaining_non_leads, non_leads)
        self.assertSetEqual(remaining_non_managers, non_managers)

        self.assertTrue(lead_and_manager <= managers)
        self.assertTrue(lead_and_manager <= leads)

    def test_clone_scope_vanilla(self):
        self.scope = self.project.clone(asynchronous=False)

        self.assertNotEqual(self.project.id, self.scope.id)
        self.assertEqual(self.project._json_data.get('tasks_count'), self.scope._json_data.get('tasks_count'))
        self.assertEqual(self.project._json_data.get('processes_count'), self.scope._json_data.get('processes_count'))
        self.assertEqual(self.project._json_data.get('activities_count'), self.scope._json_data.get('activities_count'))
        self.assertEqual(self.project._json_data.get('parts_count'), self.scope._json_data.get('parts_count'))
        self.assertEqual(self.project._json_data.get('model_parts_count'), self.scope._json_data.get('model_parts_count'))
        self.assertEqual(self.project._json_data.get('properties_count'), self.scope._json_data.get('properties_count'))

    def test_scope_delete(self):
        new_scope = self.project.clone(asynchronous=False)
        self.assertNotEqual(self.project.id, new_scope.id)
        new_scope.delete(asynchronous=False)

        with self.assertRaisesRegex(NotFoundError, 'No scope fits criteria'):
            # throw in arbitrary sleep to give backend time to actually delete the scope.
            sleep(1)
            self.client.scope(pk=new_scope.id)

    def test_clone_scope_updated_name_description_tags_etc(self):
        """
        self, source_scope, name=None, status=None, tags=None, start_date=None, due_date=None,
                    description=None, team=None, scope_options=None, async=False):
        """
        new_scope = self.project.clone(
            name="new bike scope",
            description="new description",
            status=ScopeStatus.CLOSED,
            # scope_options={"hello": "world"},
            tags=('a', 'b', 'b', 'c'),
            asynchronous=False)
        self.scope = new_scope

        self.assertNotEqual(self.project.id, new_scope.id)
        self.assertEqual(new_scope._json_data.get('name'), "new bike scope")
        self.assertEqual(new_scope._json_data.get('text'), "new description")
        self.assertEqual(new_scope._json_data.get('status'), ScopeStatus.CLOSED)
        # self.assertListEqual(new_scope._json_data.get('tags'), ["a", "b", "c"])

    def test_retrieve_scope_with_refs(self):
        # setup
        scope_ref = 'bike-project'
        scope_name = 'Bike Project'
        scope = self.client.scope(ref=scope_ref)

        # testing
        self.assertIsInstance(scope, Scope2)
        self.assertTrue(scope.name, scope_name)
