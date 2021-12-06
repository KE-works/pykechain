from typing import Optional

from pykechain.defaults import API_EXTRA_PARAMS
from pykechain.enums import FormCategory
from pykechain.models.input_checks import check_list_of_base, check_uuid
from pykechain.typing import ObjectID
from tests.classes import TestBetamax


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
