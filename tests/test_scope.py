import datetime

from pykechain.enums import ScopeStatus, KEChainPages, ScopeMemberActions, ScopeRoles
from pykechain.exceptions import NotFoundError, MultipleFoundError, IllegalArgumentError
from pykechain.models import Team, Scope2
from pykechain.models.sidebar.sidebar_manager import SideBarManager
from tests.classes import TestBetamax


class TestScopes(TestBetamax):
    """
    Test retrieval and scope attributes and methods.
    """

    def test_scope_attributes(self):
        attributes = ['_client', '_json_data', 'id', 'name', 'created_at', 'updated_at', 'ref',
                      'process', 'workflow_root', 'description', 'status', 'category', 'tags',
                      'start_date', 'due_date']

        obj = self.project
        for attribute in attributes:
            with self.subTest(attribute):
                self.assertTrue(hasattr(obj, attribute),
                                "Could not find '{}' in the object: '{}'".format(attribute, obj.__dict__.keys()))

    def test_retrieve_scopes(self):
        self.assertTrue(self.client.scopes())

    def test_retrieve_scope_with_refs(self):
        # setup
        scope_ref = 'bike-project'
        scope_name = 'Bike Project'
        scope = self.client.scope(ref=scope_ref)

        # testing
        self.assertIsInstance(scope, Scope2)
        self.assertTrue(scope.name, scope_name)

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

    def test_team_property_of_scope(self):
        """Test for the property 'team' of a scope."""
        team = self.project.team

        self.assertIsNotNone(team)
        self.assertIsInstance(team, Team)

    def test_side_bar(self):
        side_bar_manager = self.project.side_bar()

        self.assertIsInstance(side_bar_manager, SideBarManager)


class TestScopeMembers(TestBetamax):
    """
    Tests user assignment to a scope.
    """

    DEFAULTS = {
        ScopeRoles.MANAGER: [
            'superuser',
            'testmanager',
        ],
        ScopeRoles.LEADMEMBER: [
            'superuser',
            'testlead',
        ],
        ScopeRoles.MEMBER: [
            'testuser',
        ]
    }

    def _reset_members(self):
        """Reset the scope members by removing all members and adding the defaults"""
        [self.project.remove_member(member=member['username']) for member in self.project.members()]

        for role in [ScopeRoles.MANAGER, ScopeRoles.LEADMEMBER, ScopeRoles.MEMBER]:
            for member in self.DEFAULTS[role]:
                self.project._update_scope_project_team(ScopeMemberActions.ADD, role, member)

    def setUp(self):
        super().setUp()
        self._reset_members()

    def tearDown(self):
        self._reset_members()
        super().tearDown()

    def test_reset_members(self):
        """Test `_reset_members` method of the test class"""
        self.assertTrue(True)

    def test_members(self):
        scope = self.project

        # Helper function:
        def get_member_names(**kwargs):
            return [member['username'] for member in scope.members(**kwargs)]

        all_members = set(get_member_names())
        managers = set(get_member_names(is_manager=True))
        non_managers = set(get_member_names(is_manager=False))
        leads = set(get_member_names(is_leadmember=True))
        non_leads = set(get_member_names(is_leadmember=False))
        basic_members = set(get_member_names(is_manager=False, is_leadmember=False))
        lead_and_manager = set(get_member_names(is_manager=True, is_leadmember=True))

        self.assertEqual(4, len(all_members), msg=','.join(all_members))
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

    def test_add_member(self):
        member_to_be_added = 'anotheruser'
        self.project.add_member(member_to_be_added)
        self.project = self.client.scope(pk=self.project.id)
        project_members = self.project.members()

        # testing
        self.assertTrue(member_to_be_added in [member['username'] for member in project_members])

    def test_add_member_by_id(self):
        member_id = 4
        with self.assertRaises(IllegalArgumentError):
            # noinspection PyTypeChecker
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

    def test_add_leadmember(self):
        leadmember_to_be_added = 'anotheruser'
        # testing
        self.project.add_leadmember(leadmember_to_be_added)
        self.project = self.client.scope(pk=self.project.id)
        project_leadmembers = self.project.members(is_leadmember=True)
        self.assertTrue(leadmember_to_be_added in [leadmember['username'] for leadmember in project_leadmembers])

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


class TestScopeEdit(TestBetamax):
    """
    Test modifications to a scope.
    """

    def setUp(self):
        super().setUp()
        testing_project = self.project
        self.project = None
        self.scope = testing_project.clone()

    def tearDown(self):
        if self.scope:
            self.scope.delete()
        super().tearDown()

    # 2.2.0+
    # noinspection PyTypeChecker
    def test_edit_scope(self):
        # setUp
        new_scope_name = 'Pykechain testing (bike project)'
        new_scope_description = 'Project used to build a Bike. Part-time job is to also test Pykechain.'
        new_start_date = datetime.datetime(2018, 12, 5, tzinfo=None)
        new_due_date = datetime.datetime(2018, 12, 8, tzinfo=None)
        new_tags = ['tag_one', 'tag_two']

        self.scope.edit(
            name=new_scope_name,
            description=new_scope_description,
            start_date=new_start_date,
            due_date=new_due_date,
            status=ScopeStatus.CLOSED,
            tags=new_tags,
        )

        retrieved_project = self.client.scope(id=self.scope.id, status=ScopeStatus.CLOSED)
        
        # testing
        self.assertEqual(new_scope_name, retrieved_project.name)
        self.assertEqual(new_scope_description, retrieved_project.description)
        self.assertIn(retrieved_project._json_data['start_date'], ('2018-12-05T00:00:00Z', '2018-12-05T00:00:00+00:00'))
        self.assertIn(retrieved_project._json_data['due_date'], ('2018-12-08T00:00:00Z', '2018-12-08T00:00:00+00:00'))
        self.assertEqual(ScopeStatus.CLOSED, retrieved_project.status)
        self.assertEqual(new_tags, retrieved_project.tags)

        with self.assertRaises(IllegalArgumentError):
            self.scope.edit(name=True)

        with self.assertRaises(IllegalArgumentError):
            self.scope.edit(description=new_start_date)

        with self.assertRaises(IllegalArgumentError):
            self.scope.edit(start_date='Yes, man!')

        with self.assertRaises(IllegalArgumentError):
            self.scope.edit(due_date='Wrong')

        with self.assertRaises(IllegalArgumentError):
            self.scope.edit(status='ILLEGAL_STATUS_WILL_CAUSE_ERR')

        with self.assertRaises(IllegalArgumentError):
            self.scope.edit(tags='tags must be a list of strings')

    # v2.3.3
    def test_edit_scope_team(self):
        """Test capabilities of changing team scope"""

        team_one, team_two = self.client.teams()[:2]

        self.scope.edit(team=team_one)
        self.assertEqual(self.scope.team, team_one)

        self.scope.edit(team=team_two)
        self.assertEqual(self.scope.team, team_two)

    def test_set_landing_page(self):
        tasks = [
            self.scope.activities()[0],
            KEChainPages.DATA_MODEL,
        ]

        for task in tasks:
            with self.subTest(msg=task):
                self.scope.set_landing_page(activity=task)
