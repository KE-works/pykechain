from pykechain.enums import TeamRoles
from pykechain.exceptions import NotFoundError, MultipleFoundError, IllegalArgumentError
from pykechain.models import User
from pykechain.models.team import Team
from tests.classes import TestBetamax


class TestTeams(TestBetamax):
    def setUp(self):
        super().setUp()

        self.required_kwargs = dict(
            name="_test team", user=self.client.user("testuser")  # type: User
        )

        self.team = self.client.create_team(**self.required_kwargs)  # type: Team

    def tearDown(self):
        self.team.delete()
        super().tearDown()

    def test_create_team(self):
        self.assertIsInstance(self.team, Team)
        self.assertEqual(len(self.team.members()), 1)
        self.assertEqual(self.team.name, "_test team")

    def test_create_team_with_inputs(self):
        # setUp
        landing_page = f"#/scopes/{self.project.id}"
        new_team = self.client.create_team(
            description="This is the description",
            options=dict(
                landingPage=landing_page,
            ),
            is_hidden=True,
            **self.required_kwargs,
        )

        # testing
        self.assertEqual(new_team.description, "This is the description")
        self.assertDictEqual(new_team.options, {"landingPage": landing_page})
        self.assertTrue(new_team.is_hidden)

        # tearDown
        new_team.delete()

    def test_create_team_incorrect_inputs(self):
        with self.assertRaises(IllegalArgumentError):
            self.client.create_team(description=1, **self.required_kwargs)
        with self.assertRaises(IllegalArgumentError):
            self.client.create_team(options=f"#/scopes/{self.project.id}", **self.required_kwargs)
        with self.assertRaises(IllegalArgumentError):
            self.client.create_team(is_hidden="False", **self.required_kwargs)

    def test_retrieve_teams(self):
        self.assertTrue(self.client.teams())

    def test_retrieve_single_unknown_team(self):
        with self.assertRaises(NotFoundError):
            self.client.team("This is not a existing team name for sure")

    def test_retrieve_single_multiple_team_raises_error(self):
        with self.assertRaises(MultipleFoundError):
            self.client.team()

    def test_retrieve_single_team_with_known_teamname(self):
        self.assertTrue(self.client.team(name="_test team"))

    def test_retrieve_members(self):
        members = self.team.members()
        self.assertTrue(len(members) > 0)

    def test_retrieve_managers_members_owners(self):
        all_members = self.team.members()

        manager = self.team.members(role=TeamRoles.MANAGER)
        self.assertTrue(len(manager) >= 0)

        owner = self.team.members(role=TeamRoles.OWNER)
        self.assertTrue(len(owner) > 0)

        members = self.team.members(role=TeamRoles.MEMBER)
        self.assertTrue(len(owner) > 0)

        self.assertEqual(len(all_members), len(manager) + len(owner) + len(members))

    def test_retrieve_member_with_invalid_role(self):
        with self.assertRaisesRegex(IllegalArgumentError, "must be an option from enum"):
            self.team.members(role="FOOBARROLE")

    def test_add_and_remove_member(self):
        members = self.team.members()
        a_user = self.client.user(username="anotheruser")

        self.team.add_members([a_user.id], role=TeamRoles.MEMBER)

        self.assertIn(
            a_user.id, [member.get("pk") for member in self.team.members(role=TeamRoles.MEMBER)]
        )

        self.team.remove_members([a_user.id])

        self.assertListEqual(members, self.team.members())

    def test_add_scope_to_team(self):
        # setup
        self.project.edit(team=self.team.id)
        self.assertEqual(self.project.team, self.team)

        # check
        team_scopes = self.team.scopes()
        self.assertEqual([t.id for t in team_scopes], [self.project.id])

    def test_team_attributes(self):
        attributes = ["_client", "_json_data", "id", "name", "created_at", "updated_at", "ref"]

        obj = self.team
        for attribute in attributes:
            self.assertTrue(
                hasattr(obj, attribute),
                f"Could not find '{attribute}' in the object: '{obj.__dict__}'",
            )

    def test_team_edit(self):
        # setUp
        options = dict(landingPage=f"#/scopes/{self.project.id}")
        self.team.edit(
            name="renamed team",
            description="My team description",
            options=options,
            is_hidden=True,
        )

        # testing
        self.assertEqual(self.team.name, "renamed team")
        self.assertEqual(self.team.description, "My team description")
        self.assertDictEqual(self.team.options, options)
        self.assertTrue(self.team.is_hidden)

    # noinspection PyTypeChecker
    def test_team_edit_wrong_inputs(self):
        with self.assertRaises(IllegalArgumentError):
            self.team.edit(name=123)
        with self.assertRaises(IllegalArgumentError):
            self.team.edit(description=False)
        with self.assertRaises(IllegalArgumentError):
            self.team.edit(options="New scope")
        with self.assertRaises(IllegalArgumentError):
            self.team.edit(is_hidden=1)
