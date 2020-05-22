import pytest
from envparse import env

from pykechain import get_project
from pykechain.enums import KechainEnv
from pykechain.exceptions import ClientError
from tests.classes import TestBetamax
from tests.utils import TEST_TOKEN, TEST_URL, TEST_SCOPE_NAME, TEST_SCOPE_ID

PSEUDO_TOKEN = 'aabbccddeeffgg0011223344556677889900'
PSEUDO_PASSWORD = 'abc123!@#'
PSEUDO_SCOPE_ID = 'eeb0937b-da50-4eb2-8d74-f36259cca96e'


@pytest.mark.skipif("os.getenv('TRAVIS', False) or os.getenv('GITHUB_ACTIONS', False)",
                    reason="Skipping tests when using Travis or Github Actions, as not Auth can be provided")
class TestGetProjectHelperNotForTravis(TestBetamax):
    def setUp(self):
        super(TestGetProjectHelperNotForTravis, self).setUp()
        # unset all environment variables in the self.env protected env world
        for kec_env in KechainEnv.values():
            self.env.unset(kec_env)

    def test_get_project__not_for_travis(self):
        self.env.set(KechainEnv.KECHAIN_FORCE_ENV_USE, "false")
        with self.env:
            project = get_project(TEST_URL, token=TEST_TOKEN, scope=TEST_SCOPE_NAME)
            self.assertEqual(project.name, TEST_SCOPE_NAME)

    # 1.12.1
    def test_get_project__force_env_use_no_vars(self):
        """Test the get_project by using KECHAIN_FORCE_ENV_USE=True"""
        self.env.set('KECHAIN_FORCE_ENV_USE', 'True')
        with self.env:
            self.assertTrue(env.bool(KechainEnv.KECHAIN_FORCE_ENV_USE))

            with self.assertRaisesRegex(ClientError, "should be provided as environment variable"):
                # KECHAIN_SCOPE or KECHAIN_SCOPE_ID should be provided as environment variable
                get_project()

    def test_get_project__force_env_use__only_url(self):
        self.env.update(dict(KECHAIN_URL=TEST_URL,
                             KECHAIN_FORCE_ENV_USE='True'))
        with self.env:
            self.assertTrue(env.bool(KechainEnv.KECHAIN_FORCE_ENV_USE))
            with self.assertRaisesRegex(ClientError, "should be provided as environment variable"):
                # Error: KECHAIN_SCOPE or KECHAIN_SCOPE_ID should be provided as environment variable
                get_project()

    def test_get_project__force_env_use__url_and_token(self):
        self.env.update(dict(KECHAIN_URL=TEST_URL,
                             KECHAIN_TOKEN=TEST_TOKEN,
                             KECHAIN_FORCE_ENV_USE='True'))
        with self.env:
            self.assertTrue(env.bool(KechainEnv.KECHAIN_FORCE_ENV_USE))
            with self.assertRaisesRegex(ClientError, "should be provided as environment variable"):
                # Error: KECHAIN_SCOPE or KECHAIN_SCOPE_ID should be provided as environment variable
                get_project()

    def test_get_project__force_env_use__url_token_and_name(self):
        self.env.update(dict(KECHAIN_URL=TEST_URL,
                             KECHAIN_TOKEN=TEST_TOKEN,
                             KECHAIN_SCOPE_ID=TEST_SCOPE_ID,
                             KECHAIN_FORCE_ENV_USE='True'))
        with self.env:
            self.assertTrue(env.bool(KechainEnv.KECHAIN_FORCE_ENV_USE))
            self.assertEqual(get_project().name, TEST_SCOPE_NAME)

    def test_get_project__force_env_use__other_things_provided(self):
        self.env.update(dict(KECHAIN_URL=TEST_URL,
                             KECHAIN_TOKEN=TEST_TOKEN,
                             KECHAIN_SCOPE_ID=TEST_SCOPE_ID,
                             KECHAIN_FORCE_ENV_USE='True'))
        with self.env:
            self.assertTrue(env.bool(KechainEnv.KECHAIN_FORCE_ENV_USE))
            self.assertEqual(get_project(url='http://whatever', token=PSEUDO_TOKEN).name, TEST_SCOPE_NAME)

    def test_test_get_project_with_scope_id__not_for_travis(self):
        project = get_project(TEST_URL, token=TEST_TOKEN, scope_id=TEST_SCOPE_ID)
        self.assertEqual(project.name, TEST_SCOPE_NAME)

    def test_get_project_from_env__not_for_travis(self):
        # setup
        self.env.update(dict(KECHAIN_URL=TEST_URL,
                             KECHAIN_TOKEN=TEST_TOKEN,
                             KECHAIN_SCOPE=TEST_SCOPE_NAME))

        with self.env:
            project = get_project()
            self.assertEqual(project.name, self.env['KECHAIN_SCOPE'])


class TestGetProjectHelper(TestBetamax):
    def test_project_raises_error__no_auth(self):
        with self.assertRaisesRegex(ClientError, "Error: insufficient arguments"):
            get_project(url=TEST_URL)

    def test_project_raises_error__token_and_no_scope(self):
        with self.assertRaisesRegex(ClientError, "Error: insufficient arguments"):
            get_project(url=TEST_URL, token=TEST_TOKEN)

    def test_project_raises_error__no_pass(self):
        with self.assertRaisesRegex(ClientError, "Error: insufficient arguments"):
            get_project(url=TEST_URL, username='auser', scope='Scope')

    def test_project_raises_error__auth_and_no_scope(self):
        with self.assertRaisesRegex(ClientError, "Error: insufficient arguments"):
            get_project(url=TEST_URL, username='auser', password=PSEUDO_PASSWORD)

    def test_project_raises_error__scope_id_and_no_pass(self):
        with self.assertRaisesRegex(ClientError, "Error: insufficient arguments"):
            get_project(url=TEST_URL, username='auser', scope_id=PSEUDO_SCOPE_ID)

    def test_project_raises_error__auth_and_no_url(self):
        with self.assertRaisesRegex(ClientError, "Error: insufficient arguments"):
            get_project(username='auser', password=PSEUDO_PASSWORD, scope_id=PSEUDO_SCOPE_ID)

    def test_project_raises_error__token_and_no_url(self):
        with self.assertRaisesRegex(ClientError, "Error: insufficient arguments"):
            get_project(token=PSEUDO_TOKEN, scope_id=PSEUDO_SCOPE_ID)
