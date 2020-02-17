import datetime
import time
from unittest import TestCase, skipIf, skip

import pytz
import six
import warnings

from pykechain.enums import ScopeStatus
from pykechain.models import Team
from pykechain.models.scope2 import Scope2
from pykechain.utils import parse_datetime
from pykechain.client import Client
from pykechain.exceptions import ForbiddenError, ClientError, NotFoundError, IllegalArgumentError
from tests.classes import TestBetamax
from tests.utils import TEST_FLAG_IS_WIM2

if six.PY2:
    from test.test_support import EnvironmentVarGuard
elif six.PY3:
    from test.support import EnvironmentVarGuard


class TestClient(TestCase):
    def setUp(self):
        self.env = EnvironmentVarGuard()

    def test_init_default_url(self):
        client = Client()

        self.assertEqual(client.api_root, 'http://localhost:8000/')

    def test_init_custom_url(self):
        client = Client(url='http://testing.com:1234')

        self.assertEqual(client.api_root, 'http://testing.com:1234')

    def test_init_no_login(self):
        client = Client()

        self.assertNotIn('Authorization', client.headers)
        self.assertIsNone(client.auth)

    def test_init_basic_auth(self):
        client = Client()

        client.login('someuser', 'withpass')

        self.assertNotIn('Authorization', client.headers)
        self.assertTrue(client.auth)

    def test_init_token(self):
        client = Client()
        PSEUDO_TOKEN = '123123'

        client.login(token=PSEUDO_TOKEN)

        self.assertTrue(client.headers['Authorization'], 'Token {}'.format(PSEUDO_TOKEN))
        self.assertIsNone(client.auth)

    def test_init_no_ssl(self):
        client = Client(check_certificates=False)

        self.assertFalse(client.session.verify)

    # 1.12
    def test_client_raises_error_with_false_url(self):
        with self.assertRaises(ClientError):
            Client(url='wrongurl')

    def test_client_from_env(self):
        """
        Test if the client does not provide a warning when no env file can be found

            Userwarning: 'Could not any envfile.'
            '.../lib/python3.5/site-packages/envparse.py'
        """
        self.env.set('KECHAIN_URL', 'http://localhost:8000')
        with self.env:
            with warnings.catch_warnings(record=True) as captured_warnings:
                client = Client.from_env()
                self.assertEqual(len(captured_warnings), 0)


class TestClientLive(TestBetamax):

    def setUp(self):
        """
        SetUp the test.
        """
        super(TestClientLive, self).setUp()
        self.temp_scope = None

    def tearDown(self):
        """Teardown the test, remove the scope.

        When you create a scope, assign it to self.scope such that it is deleted when the test is complete
        """
        if self.temp_scope:
            self.temp_scope.delete()
        super(TestClientLive, self).tearDown()

    def test_login(self):
        self.assertTrue(self.project.parts())

    def test_no_login(self):
        self.client.login('wrong', 'user')

        with self.assertRaises(ForbiddenError):
            self.client.parts()

    # 2.6.0
    def test_create_scope(self):
        # setUp
        client = self.client
        scope_name = 'New scope (pykchain testing - remove me)'
        scope_description = 'This is a new scope for testing'
        scope_status = ScopeStatus.ACTIVE
        scope_tags = ['test_tag', 'new_project_tag']
        scope_start_date = datetime.datetime(2019, 4, 12, tzinfo=pytz.UTC)
        scope_due_date = datetime.datetime(2020, 4, 12, tzinfo=pytz.UTC)
        scope_team = client.team(name='Team No.1')

        self.temp_scope = client.create_scope(
            name=scope_name,
            description=scope_description,
            status=scope_status,
            tags=scope_tags,
            start_date=scope_start_date,
            due_date=scope_due_date,
            team=scope_team
        )

        # testing
        self.assertEqual(self.temp_scope.name, scope_name)
        self.assertEqual(scope_start_date, parse_datetime(self.temp_scope._json_data['start_date']))
        self.assertEqual(scope_due_date, parse_datetime(self.temp_scope._json_data['due_date']))
        self.assertIn(scope_tags[0], self.temp_scope.tags)
        self.assertIn(scope_tags[1], self.temp_scope.tags)

    def test_create_scope_with_team_name(self):
        # setUp
        client = self.client

        scope_name = 'New scope with the team name'
        scope_team_name = 'Team No.1'

        self.temp_scope = client.create_scope(
            name=scope_name,
            team=scope_team_name
        )

        # testing
        self.assertTrue(self.temp_scope.team)
        self.assertTrue(isinstance(self.temp_scope.team, Team))
        self.assertEqual(self.temp_scope.team.name, scope_team_name)

    def test_create_scope_with_team_uuid(self):
        # setUp
        client = self.client

        scope_name = 'New scope with team uuid'
        scope_team_name = 'Team No.1'
        scope_team_id = client.team(name=scope_team_name).id

        self.temp_scope = client.create_scope(
            name=scope_name,
            team=scope_team_id
        )

        # testing
        self.assertTrue(self.temp_scope.team)
        self.assertTrue(isinstance(self.temp_scope.team, Team))
        self.assertEqual(self.temp_scope.team.name, scope_team_name)

    def test_create_scope_no_arguments(self):
        # setUp
        client = self.client
        self.temp_scope = client.create_scope(name='New scope no arguments')

        # testing
        self.assertEqual(self.temp_scope.name, 'New scope no arguments')
        self.assertTrue(self.temp_scope._json_data['start_date'])
        self.assertFalse(self.temp_scope.tags)

    def test_create_scope_with_wrong_arguments(self):
        # setUp
        client = self.client

        # testing
        with self.assertRaises(IllegalArgumentError):
            client.create_scope(name=12)
        with self.assertRaises(IllegalArgumentError):
            client.create_scope(name='Failed scope', status='LIMBO')
        with self.assertRaises(IllegalArgumentError):
            client.create_scope(name='Failed scope', description=True)
        with self.assertRaises(IllegalArgumentError):
            client.create_scope(name='Failed scope', tags='One tag no list')
        with self.assertRaises(IllegalArgumentError):
            client.create_scope(name='Failed scope', tags=[12, 'this', 'fails'])
        with self.assertRaises(IllegalArgumentError):
            client.create_scope(name='Failed scope', team=['Fake team'])

    def test_clone_scope(self):
        # setUp
        client = self.client
        clone = client.clone_scope(source_scope=self.project)

        # testing
        try:
            self.assertIsInstance(clone, Scope2)
            self.assertEqual(clone.name, 'CLONE - {}'.format(self.project.name))
            self.assertEqual(clone.status, self.project.status)
            self.assertEqual(clone.start_date, self.project.start_date)
            self.assertEqual(clone.due_date, self.project.due_date)
            self.assertEqual(clone.description, self.project.description)
            self.assertListEqual(clone.tags, self.project.tags)
        except Exception as e:
            clone.delete()
            raise Exception(e)

    @skip("Test does not work at all")
    def test_clone_asynchronous(self):
        """ Careful with deleting the cloned scope if async=True: The response is the source scope! """

        client = self.client
        name = '___Async cloned scope TARGETCLONE'

        original_scope = client.create_scope(
            name='___Async to be cloned scope SOURCE',
        )
        time.sleep(3)
        clone = client.clone_scope(
            name=name,
            source_scope=original_scope,
            asynchronous=True,
        )

        # testing
        self.assertIsInstance(clone, Scope2)
        self.assertEqual(original_scope.id, clone.id)

        # teardown
        counter = 0
        retrieved_clone = None
        while counter < 5:
            try:
                retrieved_clone = client.scope(name=name, counter=counter) # add counter to the query to ensure that the casettes are recorded correctly
            except NotFoundError:
                counter += 1
                time.sleep(3)
            if retrieved_clone:

                break
        self.assertIsInstance(retrieved_clone, Scope2)

    def test_clone_scope_with_arguments(self):
        # setUp
        now = datetime.datetime.now()
        name = 'test clone'
        status = ScopeStatus.CLOSED
        description = 'test description'
        tags = ['one', 'two']
        team = self.project.team

        client = self.client
        clone = client.clone_scope(
            name=name,
            source_scope=self.project,
            status=status,
            start_date=now,
            due_date=now,
            description=description,
            tags=tags,
            team=team,
        )

        try:
            self.assertIsInstance(clone, Scope2)
            self.assertEqual(clone.name, name)
            self.assertEqual(clone.status, status)
            self.assertEqual(clone.start_date, now)
            self.assertEqual(clone.due_date, now)
            self.assertEqual(clone.description, description)
            self.assertEqual(clone.team, team)
            self.assertListEqual(clone.tags, tags)
        except Exception as e:
            clone.delete()
            raise Exception(e)


@skipIf(not TEST_FLAG_IS_WIM2, reason="This tests is designed for WIM version 2, expected to fail on older WIM")
class TestClientAppVersions(TestBetamax):
    def test_retrieve_versions(self):
        """Test to retrieve the app versions from KE-chain"""
        app_versions = self.project._client.app_versions
        self.assertTrue(isinstance(app_versions, list))
        self.assertTrue(isinstance(app_versions[0], dict))
        self.assertTrue(set(app_versions[0].keys()),
                        {'app', 'label', 'version', 'major', 'minor', 'patch', 'prerelease'})

    def test_compare_versions(self):
        """Multitest to check all the matchings versions"""

        self.assertTrue(self.client.match_app_version(app='kechain2.core.wim', version='>=1.0.0'))
        self.assertTrue(self.client.match_app_version(label='wim', version='>=1.0.0'))
        self.assertFalse(self.client.match_app_version(label='wim', version='==0.0.1'))

        # value error
        # wrong version string (no semver string) to check against
        with self.assertRaises(ValueError):
            self.client.match_app_version(app='kechain2.core.wim', version='1.0')

        # right version, no operand in version
        with self.assertRaises(ValueError):
            self.client.match_app_version(app='kechain2.core.wim', version='1.0.0')

        # wrong operand (should be ==)
        with self.assertRaises(ValueError):
            self.client.match_app_version(app='kechain2.core.wim', version='=1.0.0')

        # not found a match version
        with self.assertRaises(IllegalArgumentError):
            self.client.match_app_version(app='kechain2.core.wim', version='')

        # no version found on the app kechain2.metrics
        with self.assertRaises(NotFoundError):
            self.client.match_app_version(app='kechain2.core.activitylog', version='>0.0.0', default=None)

        # no version found on the app kechain2.metrics, default = True, returns True
        self.assertTrue(self.client.match_app_version(app='kechain2.core.activitylog', version='>0.0.0', default=True))

        # no version found on the app kechain2.metrics, default = False, returns False
        self.assertFalse(self.client.match_app_version(app='kechain2.core.activitylog', version='>0.0.0', default=False))

        # no version found on the app kechain2.metrics, default = False, returns False
        # default is set to return False in the method
        self.assertFalse(self.client.match_app_version(app='kechain2.core.activitylog', version='>0.0.0'))

        # did not find the app
        with self.assertRaises(NotFoundError):
            self.client.match_app_version(app='nonexistingapp', version='>0.0.0', default=None)

        # did not find the app, but the default returns a False
        self.assertFalse(self.client.match_app_version(app='nonexistingapp', version='>0.0.0', default=False))

        # did not find the app, but the default returns a False, without providing the default, as the default is False
        self.assertFalse(self.client.match_app_version(app='nonexistingapp', version='>0.0.0'))
