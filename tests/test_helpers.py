import os
import pytest

from pykechain import get_project
from pykechain.exceptions import ClientError
from tests.classes import TestBetamax
from tests.utils import TEST_TOKEN, TEST_URL, TEST_SCOPE_NAME

ERROR_MESSAGE_REGEX = "Error: insufficient arguments"

@pytest.mark.skipif("os.getenv('TRAVIS', False)", reason="Skipping tests when using Travis, as not Auth can be provided")
class TestGetProjectHelperNotForTravis(TestBetamax):
    def test_get_project__not_for_travis(self):
        project = get_project(TEST_URL, token=TEST_TOKEN, scope=TEST_SCOPE_NAME)
        self.assertEqual(project.name, TEST_SCOPE_NAME)

    def test_get_project_from_env__not_for_travis(self):
        # setup
        saved_environment = dict(os.environ)
        os.environ['KECHAIN_URL'] = TEST_URL
        os.environ['KECHAIN_TOKEN'] = TEST_TOKEN
        os.environ['KECHAIN_SCOPE'] = TEST_SCOPE_NAME

        # do test
        project = get_project()
        self.assertEqual(project.name, os.environ['KECHAIN_SCOPE'])

        # teardown
        os.unsetenv('KECHAIN_URL')
        os.unsetenv('KECHAIN_TOKEN')
        os.unsetenv('KECHAIN_SCOPE')
        for k, v in saved_environment.items():
            os.environ[k] = v


class TestGetProjectHelper(TestBetamax):

    def test_project_raises_error__no_auth(self):
        with self.assertRaisesRegex(ClientError, ERROR_MESSAGE_REGEX):
            get_project(url=TEST_URL)

    def test_project_raises_error__token_and_no_scope(self):
        with self.assertRaisesRegex(ClientError, ERROR_MESSAGE_REGEX):
            get_project(url=TEST_URL, token=TEST_TOKEN)

    def test_project_raises_error__no_pass(self):
        with self.assertRaisesRegexp(ClientError, ERROR_MESSAGE_REGEX):
            get_project(url=TEST_URL, username='auser', scope='Scope')

    def test_project_raises_error__auth_and_no_scope(self):
        with self.assertRaisesRegexp(ClientError, ERROR_MESSAGE_REGEX):
            get_project(url=TEST_URL, username='auser', password='somepass')

    def test_project_raises_error__scope_id_and_no_pass(self):
        with self.assertRaisesRegexp(ClientError, ERROR_MESSAGE_REGEX):
            get_project(url=TEST_URL, username='auser', scope_id='234')

    def test_project_raises_error__auth_and_no_url(self):
        with self.assertRaisesRegexp(ClientError, ERROR_MESSAGE_REGEX):
            get_project(username='auser', password='somepass', scope_id='234')

    def test_project_raises_error__token_and_no_url(self):
        with self.assertRaisesRegexp(ClientError, ERROR_MESSAGE_REGEX):
            get_project(token='123', scope_id='234')

