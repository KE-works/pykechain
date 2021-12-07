import pytest

from pykechain.enums import FormCategory
from pykechain.exceptions import NotFoundError
from pykechain.models.form import Form
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

    def setUp(self):
        super().setUp()
        self.form_model: Form = self.client.form("1st", category=FormCategory.MODEL)

    def tearDown(self):
        super().tearDown()

    def test_form_attributes(self):
        attributes = [
            "_client",
            "_json_data",
            "id",
            "name",
            "created_at",
            "updated_at",
            "derived_from_id",
            "ref",
            "description",
            "active_status",
            "category",
            "tags",
            "form_model_root",
            "form_instance_root",
            "model_id",
            "scope_id",
            "status_forms",
        ]

        form_model = self.client.form("1st", category=FormCategory.MODEL)
        for attr in attributes:
            with self.subTest(attr):
                self.assertTrue(
                    hasattr(form_model, attr),
                    f"Could not find '{attr}' in the form: '{form_model.__dict__.keys()}",
                )

    def test_form_instances(self):
        with self.subTest("testing instances"):
            form_instances = self.form_model.instances()
            self.assertTrue(len(form_instances) >= 1)
            form_instance = form_instances[0]

            self.assertTrue(form_instance.category, FormCategory.INSTANCE)
            self.assertTrue(form_instance.model_id, self.form_model.id)

        with self.subTest("testing instance"):
            form_instance = self.form_model.instance()
            self.assertTrue(form_instance.category, FormCategory.INSTANCE)
            self.assertTrue(form_instance.model_id, self.form_model.id)

    def test_model_form_instantiation(self):
        form_instance = self.form_model.instantiate(name="___test form from 1st")

        self.assertTrue(form_instance.model_id, self.form_model.id)

        # delete
        form_instance.delete()

    def test_model_form_delete(self):
        form_instance = self.form_model.instantiate(name="___test form from 1st")
        self.assertTrue(form_instance.model_id, self.form_model.id)

        # delete
        form_instance.delete()
        with self.assertRaisesRegex(NotFoundError, "Could not reload Form"):
            form_instance.refresh()

    def test_model_clone(self):
        cloned_form_model = self.form_model.clone(name="___ test clone form 1st", target_scope=self.project)
        self.assertTrue(cloned_form_model)

        # delete
        cloned_form_model.delete()
