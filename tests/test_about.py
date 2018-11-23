from unittest import TestCase


class TestAbout(TestCase):
    def test_import(self):
        from pykechain import __about__ as about

        self.assertTrue(about)

    def test_names(self):
        from pykechain import __about__ as about

        self.assertTrue(about.name)
        self.assertTrue(about.version)
        import semver
        self.assertTrue(semver.parse(about.version))
