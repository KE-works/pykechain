import pytest

from pykechain.enums import FormCategory
from tests.classes import TestBetamax


@pytest.mark.skipif(
    "os.getenv('GITHUB_ACTIONS', False)",
    reason="Skipping tests when using Travis or Github Actions "
           "as there is no public forms world yet",
)
class TestForms(TestBetamax):
    """
    Test retrieval and scope attributes and methods.
    """

    def test_froms_attributes(self):
        attributes = [
            "_client",
            "_json_data",
            "id",
            "name",
            "created_at",
            "updated_at",
            "ref",
            "description",
            "active_status",
            "category",
            "tags",
        ]

        obj = self.client.form("1st", category=FormCategory.MODEL)
        for attr in attributes:
            with self.subTest(attr):
                self.assertTrue(
                    hasattr(obj, attr),
                    f"Could not find '{attr}' in the form: '{obj.__dict__.keys()}",
                )
