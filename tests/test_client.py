import datetime
import time
import warnings
from unittest import TestCase

import pytz

from pykechain.client import Client
from pykechain.enums import ScopeStatus
from pykechain.exceptions import (
    APIError,
    ClientError,
    ForbiddenError,
    IllegalArgumentError,
    NotFoundError,
)
from pykechain.models import Base, Team
from pykechain.models.scope import Scope
from tests.classes import EnvironmentVarGuard, TestBetamax


class TestClient(TestCase):
    def setUp(self):
        self.env = EnvironmentVarGuard()

    def test_init_default_url(self):
        client = Client()

        self.assertEqual(client.api_root, "http://localhost:8000/")

    def test_init_custom_url(self):
        client = Client(url="http://testing.com:1234")

        self.assertEqual(client.api_root, "http://testing.com:1234")

    def test_init_no_login(self):
        client = Client()

        self.assertNotIn("Authorization", client.headers)
        self.assertIsNone(client.auth)

    def test_init_basic_auth(self):
        client = Client()

        client.login("someuser", "withpass")

        self.assertNotIn("Authorization", client.headers)
        self.assertTrue(client.auth)

    def test_init_token(self):
        client = Client()
        PSEUDO_TOKEN = "123123"

        client.login(token=PSEUDO_TOKEN)

        self.assertTrue(client.headers["Authorization"], f"Token {PSEUDO_TOKEN}")
        self.assertIsNone(client.auth)

    def test_init_no_ssl(self):
        client = Client(check_certificates=False)

        self.assertFalse(client.session.verify)

    # 1.12
    def test_client_raises_error_with_false_url(self):
        with self.assertRaises(ClientError):
            Client(url="wrongurl")

    def test_client_from_env(self):
        """
        Test if the client does not provide a warning when no env file can be found

            Userwarning: 'Could not any envfile.'
            '.../lib/python3.5/site-packages/envparse.py'
        """
        self.env.set("KECHAIN_URL", "http://localhost:8000")
        with self.env:
            with warnings.catch_warnings(record=True) as captured_warnings:
                client = Client.from_env()
                self.assertEqual(len(captured_warnings), 0)

    # noinspection PyTypeChecker
    def test_reload(self):
        client = Client()

        not_a_kechain_object = 3
        with self.assertRaises(
            IllegalArgumentError, msg="Reload must receive an object of type Base."
        ):
            client.reload(not_a_kechain_object)

        empty_kechain_object = Base(json=dict(name="empty", id="1234567890"), client=client)
        with self.assertRaises(
            IllegalArgumentError, msg="Reload cant find API resource for type Base"
        ):
            client.reload(empty_kechain_object)


class TestClientLive(TestBetamax):
    def setUp(self):
        super().setUp()
        self.temp_scope = None

    def tearDown(self):
        """Teardown the test, remove the scope.

        When you create a scope, assign it to self.temp_scope such that it is deleted when the test is complete
        """
        if self.temp_scope:
            self.temp_scope.delete()
        super().tearDown()

    def test_login(self):
        self.assertTrue(self.project.parts())

    def test_no_login(self):
        self.client.login("wrong", "user")

        with self.assertRaises(ForbiddenError):
            self.client.parts()

    # 3.6.3
    def test_get_current_user(self):
        user = self.client.current_user()

        from pykechain.models import User

        self.assertIsInstance(user, User)

        self.client.auth = None
        self.client.headers = None
        with self.assertRaises(APIError):
            self.client.current_user()

    # 3.7.0
    def test_reload_deleted_object(self):
        bike_model = self.project.model(name="Bike")
        bike = bike_model.instance()
        wheel_model = bike_model.child(name="Wheel")

        wheel_name = "__new wheel: test for reloading"
        new_wheel_1 = bike.add(name=wheel_name, model=wheel_model)
        new_wheel_2 = self.project.part(name=wheel_name)

        self.assertFalse(new_wheel_1 is new_wheel_2, "Parts must be separate in Python memory")
        self.assertEqual(new_wheel_1, new_wheel_2, "Parts must be identical in UUIDs")

        new_wheel_2.delete()
        with self.assertRaises(NotFoundError):
            self.project.part(name=wheel_name)

        with self.assertRaises(NotFoundError, msg="Wheel cant be reloaded after it was deleted"):
            self.client.reload(new_wheel_1)

    # 2.6.0
    def test_create_scope(self):
        # setUp
        client = self.client
        scope_name = "New scope (pykechain testing - remove me)"
        scope_description = "This is a new scope for testing"
        scope_status = ScopeStatus.ACTIVE
        scope_tags = ["test_tag", "new_project_tag"]
        scope_start_date = datetime.datetime(2019, 4, 12, tzinfo=pytz.UTC)
        scope_due_date = datetime.datetime(2020, 4, 12, tzinfo=pytz.UTC)
        scope_team = client.teams()[0]

        self.temp_scope = client.create_scope(
            name=scope_name,
            description=scope_description,
            status=scope_status,
            tags=scope_tags,
            start_date=scope_start_date,
            due_date=scope_due_date,
            team=scope_team,
        )

        # testing
        self.assertEqual(self.temp_scope.name, scope_name)
        self.assertEqual(scope_start_date, self.temp_scope.start_date)
        self.assertEqual(scope_due_date, self.temp_scope.due_date)
        self.assertIn(scope_tags[0], self.temp_scope.tags)
        self.assertIn(scope_tags[1], self.temp_scope.tags)
        self.assertEqual(scope_team, self.temp_scope.team)

    def test_create_scope_with_team_name(self):
        # setUp
        team_name = self.client.teams()[0].name

        self.temp_scope = self.client.create_scope(
            name="New scope using the team name", team=team_name
        )

        # testing
        self.assertTrue(self.temp_scope.team)
        self.assertIsInstance(self.temp_scope.team, Team)
        self.assertEqual(team_name, self.temp_scope.team.name)

    def test_create_scope_with_team_uuid(self):
        # setUp
        team_id = self.client.teams()[0].id

        self.temp_scope = self.client.create_scope(
            name="New scope using the team ID", team=team_id
        )

        # testing
        self.assertTrue(self.temp_scope.team)
        self.assertIsInstance(self.temp_scope.team, Team)
        self.assertEqual(team_id, self.temp_scope.team.id)

    def test_create_scope_no_arguments(self):
        # setUp
        self.temp_scope = self.client.create_scope(name="New scope no arguments")

        # testing
        self.assertEqual(self.temp_scope.name, "New scope no arguments")
        self.assertTrue(self.temp_scope._json_data["start_date"])
        self.assertFalse(self.temp_scope.tags)

    # noinspection PyTypeChecker
    def test_create_scope_with_wrong_arguments(self):
        # testing
        with self.assertRaises(IllegalArgumentError):
            self.client.create_scope(name=12)
        with self.assertRaises(IllegalArgumentError):
            self.client.create_scope(name="Failed scope", status="LIMBO")
        with self.assertRaises(IllegalArgumentError):
            self.client.create_scope(name="Failed scope", description=True)
        with self.assertRaises(IllegalArgumentError):
            self.client.create_scope(name="Failed scope", tags="One tag no list")
        with self.assertRaises(IllegalArgumentError):
            self.client.create_scope(name="Failed scope", tags=[12, "this", "fails"])
        with self.assertRaises(IllegalArgumentError):
            self.client.create_scope(name="Failed scope", team=["Fake team"])

    def test_clone_scope(self):
        # setUp
        self.temp_scope = self.client.clone_scope(source_scope=self.project)

        # testing
        self.assertIsInstance(self.temp_scope, Scope)
        self.assertEqual(self.temp_scope.name, f"CLONE - {self.project.name}")
        self.assertEqual(self.temp_scope.status, self.project.status)
        self.assertEqual(self.temp_scope.start_date, self.project.start_date)
        self.assertEqual(self.temp_scope.due_date, self.project.due_date)
        self.assertEqual(self.temp_scope.description, self.project.description)
        self.assertListEqual(self.temp_scope.tags, self.project.tags)

    def test_clone_scope_with_arguments(self):
        # setUp
        now = datetime.datetime.now()
        name = "test clone"
        status = ScopeStatus.CLOSED
        description = "test description"
        tags = ["one", "two"]
        team = self.project.team

        self.temp_scope = self.client.clone_scope(
            name=name,
            source_scope=self.project,
            status=status,
            start_date=now,
            due_date=now,
            description=description,
            tags=tags,
            team=team,
        )

        self.assertIsInstance(self.temp_scope, Scope)
        self.assertEqual(self.temp_scope.name, name)
        self.assertEqual(self.temp_scope.status, status)
        self.assertEqual(self.temp_scope.start_date, now)
        self.assertEqual(self.temp_scope.due_date, now)
        self.assertEqual(self.temp_scope.description, description)
        self.assertEqual(self.temp_scope.team, team)
        self.assertListEqual(self.temp_scope.tags, tags)

    def test_scope_delete(self):
        new_scope = self.project.clone(asynchronous=False)
        self.assertNotEqual(self.project.id, new_scope.id)
        new_scope.delete(asynchronous=False)

        with self.assertRaisesRegex(NotFoundError, "fit criteria"):
            # throw in arbitrary sleep to give backend time to actually delete the scope.
            time.sleep(1)
            self.client.scope(pk=new_scope.id)


class TestCloneScopeAsync(TestBetamax):
    def setUp(self):
        super().setUp()
        self.temp_scope = None
        self.source = self.client.create_scope(
            name="_Async to be cloned scope SOURCE",
        )
        time.sleep(3)

    def tearDown(self):
        self.source.delete()
        if self.temp_scope:
            self.temp_scope.delete()
        super().tearDown()

    def test_clone_asynchronous(self):
        # setUp
        clone_name = "_Async cloned scope TARGET"

        self.client.clone_scope(
            name=clone_name,
            source_scope=self.source,
            asynchronous=True,
        )

        for _ in range(5):
            try:
                self.temp_scope = self.client.scope(name=clone_name)
            except NotFoundError:
                time.sleep(3)
                continue
            else:
                break

        # testing
        self.assertIsInstance(self.temp_scope, Scope)


class TestClientAppVersions(TestBetamax):
    def test_retrieve_versions(self):
        """Test to retrieve the app versions from KE-chain"""
        app_versions = self.project._client.app_versions
        self.assertTrue(isinstance(app_versions, list))
        self.assertTrue(isinstance(app_versions[0], dict))
        self.assertTrue(
            set(app_versions[0].keys()),
            {"app", "label", "version", "major", "minor", "patch", "prerelease"},
        )

    def test_compare_versions(self):
        """Multitest to check all the matchings versions"""

        self.assertTrue(self.client.match_app_version(app="kechain2.core.wim", version=">=1.0.0"))
        self.assertTrue(self.client.match_app_version(label="wim", version=">=1.0.0"))
        self.assertFalse(self.client.match_app_version(label="wim", version="==0.0.1"))

        # value error
        # wrong version string (no semver string) to check against
        with self.assertRaises(ValueError):
            self.client.match_app_version(app="kechain2.core.wim", version="1.0")

        # right version, no operand in version
        with self.assertRaises(ValueError):
            self.client.match_app_version(app="kechain2.core.wim", version="1.0.0")

        # wrong operand (should be ==)
        with self.assertRaises(ValueError):
            self.client.match_app_version(app="kechain2.core.wim", version="=1.0.0")

        # not found a match version
        with self.assertRaises(IllegalArgumentError):
            self.client.match_app_version(app="kechain2.core.wim", version="")

        # no version found on the app kechain2.metrics
        with self.assertRaises(NotFoundError):
            self.client.match_app_version(
                app="kechain2.core.activitylog", version=">0.0.0", default=None
            )

        # no version found on the app kechain2.metrics, default = True, returns True
        self.assertTrue(
            self.client.match_app_version(
                app="kechain2.core.activitylog", version=">0.0.0", default=True
            )
        )

        # no version found on the app kechain2.metrics, default = False, returns False
        self.assertFalse(
            self.client.match_app_version(
                app="kechain2.core.activitylog", version=">0.0.0", default=False
            )
        )

        # no version found on the app kechain2.metrics, default = False, returns False
        # default is set to return False in the method
        self.assertFalse(
            self.client.match_app_version(app="kechain2.core.activitylog", version=">0.0.0")
        )

        # did not find the app
        with self.assertRaises(NotFoundError):
            self.client.match_app_version(app="nonexistingapp", version=">0.0.0", default=None)

        # did not find the app, but the default returns a False
        self.assertFalse(
            self.client.match_app_version(app="nonexistingapp", version=">0.0.0", default=False)
        )

        # did not find the app, but the default returns a False, without providing the default, as the default is False
        self.assertFalse(self.client.match_app_version(app="nonexistingapp", version=">0.0.0"))
