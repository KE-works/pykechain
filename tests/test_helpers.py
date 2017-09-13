from unittest import TestCase

import os

from pykechain import get_project
from pykechain.exceptions import ClientError
from tests.classes import TestBetamax
from tests.utils import TEST_TOKEN, TEST_URL, TEST_SCOPE_NAME


class TestGetProjectHelper(TestBetamax):
    def test_get_project_not_for_travis(self):
        if os.getenv('TRAVIS') and os.getenv('INATEST'):
            # suppress the test if running in travise
            return True

        project = get_project(TEST_URL, token=TEST_TOKEN, scope=TEST_SCOPE_NAME)
        self.assertEqual(project.name, TEST_SCOPE_NAME)

    def test_get_project_not_enough_args_raises_error(self):
        with self.assertRaisesRegex(ClientError, "sufficient arguments"):
            get_project(url=TEST_URL)

    def test_get_project_from_env(self):
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
