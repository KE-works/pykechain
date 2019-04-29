import datetime
from unittest import TestCase, skipIf

import six
import warnings

from pykechain.enums import ScopeStatus
from pykechain.models import Team
from tests.utils import TEST_FLAG_IS_WIM2

if six.PY2:
    from test.test_support import EnvironmentVarGuard
elif six.PY3:
    from test.support import EnvironmentVarGuard

from pykechain.client import Client
from pykechain.exceptions import ForbiddenError, ClientError, NotFoundError, IllegalArgumentError
from tests.classes import TestBetamax


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
    def test_login(self):
        self.assertTrue(self.client.parts())

    def test_no_login(self):
        self.client.login('wrong', 'user')

        with self.assertRaises(ForbiddenError):
            self.client.parts()

    # 2.6.0
    def test_create_scope(self):
        # setUp
        client = self.client
        scope_name = 'New scope'
        scope_description = 'This is a new scope for testing'
        scope_status = ScopeStatus.CLOSED
        scope_tags = ['test_tag', 'new_project_tag']
        scope_start_date = datetime.datetime(2019, 4, 12)
        scope_due_date = datetime.datetime(2020, 4, 12)
        scope_team = client.team(name='Team No.1')

        new_scope = client.create_scope(name=scope_name,
                                        description=scope_description,
                                        status=scope_status,
                                        tags=scope_tags,
                                        start_date=scope_start_date,
                                        due_date=scope_due_date,
                                        team=scope_team
                                        )

        # testing
        self.assertEqual(new_scope.name, scope_name)
        self.assertEqual(new_scope._json_data['start_date'], scope_start_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
        self.assertEqual(new_scope._json_data['due_date'], scope_due_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
        self.assertIn(scope_tags[0], new_scope.tags)
        self.assertIn(scope_tags[1], new_scope.tags)

        # tearDown
        client.delete_scope(scope=new_scope)

    def test_create_scope_with_team_name(self):
        # setUp
        client = self.client

        scope_name = 'New scope with the team name'
        scope_team_name = 'Team No.1'

        new_scope = client.create_scope(name=scope_name,
                                        team=scope_team_name
                                        )

        # testing
        self.assertTrue(new_scope.team)
        self.assertTrue(isinstance(new_scope.team, Team))
        self.assertEqual(new_scope.team.name, scope_team_name)

        # tearDown
        client.delete_scope(scope=new_scope)

    def test_create_scope_with_team_uuid(self):
        # setUp
        client = self.client

        scope_name = 'New scope with team uuid'
        scope_team_name = 'Team No.1'
        scope_team_id = client.team(name=scope_team_name).id

        new_scope = client.create_scope(name=scope_name,
                                        team=scope_team_id
                                        )

        # testing
        self.assertTrue(new_scope.team)
        self.assertTrue(isinstance(new_scope.team, Team))
        self.assertEqual(new_scope.team.name, scope_team_name)

        # tearDown
        client.delete_scope(scope=new_scope)

    def test_create_scope_no_arguments(self):
        # setUp
        client = self.client
        new_scope = client.create_scope(name='New scope no arguments')

        # testing
        self.assertEqual(new_scope.name, 'New scope no arguments')
        self.assertTrue(new_scope._json_data['start_date'])
        self.assertFalse(new_scope.tags)

        # tearDown
        client.delete_scope(scope=new_scope)

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
            self.client.match_app_version(app='kechain2.metrics', version='>0.0.0', default=None)

        # no version found on the app kechain2.metrics, default = True, returns True
        self.assertTrue(self.client.match_app_version(app='kechain2.metrics', version='>0.0.0', default=True))

        # no version found on the app kechain2.metrics, default = False, returns False
        self.assertFalse(self.client.match_app_version(app='kechain2.metrics', version='>0.0.0', default=False))

        # no version found on the app kechain2.metrics, default = False, returns False
        # default is set to return False in the method
        self.assertFalse(self.client.match_app_version(app='kechain2.metrics', version='>0.0.0'))

        # did not find the app
        with self.assertRaises(NotFoundError):
            self.client.match_app_version(app='nonexistingapp', version='>0.0.0', default=None)

        # did not find the app, but the default returns a False
        self.assertFalse(self.client.match_app_version(app='nonexistingapp', version='>0.0.0', default=False))

        # did not find the app, but the default returns a False, without providing the default, as the default is False
        self.assertFalse(self.client.match_app_version(app='nonexistingapp', version='>0.0.0'))
