from pykechain.enums import TeamRoles
from pykechain.exceptions import NotFoundError, MultipleFoundError, IllegalArgumentError
from pykechain.models.team import Team
from tests.classes import TestBetamax


class TestTeams(TestBetamax):

    def setUp(self):
        super(TestTeams, self).setUp()
        self.team = self.client.team(name='KE-works Team') # type: Team

    def test_retrieve_teams(self):
        self.assertTrue(self.client.teams())

    def test_retrieve_single_unknown_team(self):
        with self.assertRaises(NotFoundError):
            self.client.team('123lladadwd')

    def test_retrieve_single_multiple_team_raises_error(self):
        with self.assertRaises(MultipleFoundError):
            self.client.team()

    def test_retrieve_single_team_with_known_teamname(self):
        self.assertTrue(self.client.team(name="Team B"))

    def test_retrieve_members(self):
        members = self.team.members()
        self.assertTrue(len(members) > 0)

    def test_retrieve_managers_members_owners(self):
        all_members = self.team.members()

        manager = self.team.members(role=TeamRoles.MANAGER)
        self.assertTrue(len(manager) > 0)

        owner = self.team.members(role=TeamRoles.OWNER)
        self.assertTrue(len(owner) > 0)

        members = self.team.members(role=TeamRoles.MEMBER)
        self.assertTrue(len(owner) > 0)

        self.assertEqual(len(all_members), len(manager)+len(owner)+len(members))

    def test_retrieve_member_with_invalid_role(self):
        with self.assertRaisesRegex(IllegalArgumentError, 'role should be one of `TeamRoles`'):
            self.team.members(role="FOOBARROLE")


    def test_add_and_remove_member(self):
        members = self.team.members()
        a_user = self.client.user(username='anotheruser')

        self.team.add_members([a_user.id], role=TeamRoles.MEMBER)
        # self.team.refresh()

        self.assertIn(a_user.id,[member.get('pk') for member in self.team.members(role=TeamRoles.MEMBER)])

        self.team.remove_members([a_user.id])
        # self.team.refresh()

        self.assertListEqual(self.team.members(), members)

    def test_team_associated_scopes(self):
        team_scopes = self.team.scopes()
        self.assertEqual([t.id for t in team_scopes], [t.get('id') for t in self.team._json_data.get('scopes')])

    def test_add_scope_to_team(self):
        #setup
        old_team = self.project._json_data.get('team')

        self.project.edit(team=self.team.id)
        self.assertEqual(self.project._json_data.get('team').get('id'), self.team.id)

        # check
        self.assertEqual([t.id for t in self.team.scopes()], [self.project.id])

        #teardown
        self.project.edit(team=old_team.get('id'))