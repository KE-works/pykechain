from unittest import TestCase


class TestAbout(TestCase):

    def test_import(self):
        from pykechain import __about__ as about

        assert about

    def test_names(self):
        from pykechain import __about__ as about

        assert about.name
        assert about.version
