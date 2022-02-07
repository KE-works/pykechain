import pytest

from pykechain.enums import FormCategory, WorkflowCategory
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
        self.workflow = self.client.workflow(
            name='Simple Form Flow',
            category=WorkflowCategory.CATALOG
        )
        self.approval_workflow = self.client.workflow(
            name='Strict Approval Workflow',
            category=WorkflowCategory.CATALOG
        )
        self.discipline_context = self.project.context(
            name="Discipline 1"
        )
        self.asset_context = self.project.context(
            name="Object 1"
        )
        self.form_model_name = "__TEST__FORM_MODEL"
        self.form_model_name_2 = "__TEST__FORM_MODEL_2"

        self.form_model = self.client.create_form_model(
            name=self.form_model_name,
            scope=self.project,
            workflow=self.workflow,
            category=FormCategory.MODEL,
            contexts=[self.asset_context, self.discipline_context])
        self.form_model_2 = self.project.create_form_model(
            name=self.form_model_name_2,
            workflow=self.workflow,
            category=FormCategory.MODEL,
            contexts=[self.asset_context])
        self.form_instance = self.form_model.instantiate(name="__TEST_FORM_INSTANCE")

    def tearDown(self):
        super().tearDown()
        if self.form_instance:
            self.form_instance.delete()
        if self.form_model:
            self.form_model.delete()
        if self.form_model_2:
            self.form_model_2.delete()
        if self.test_form_instance:
            self.test_form_instance.delete()

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

        for attr in attributes:
            with self.subTest(attr):
                self.assertTrue(
                    hasattr(self.form_model, attr),
                    f"Could not find '{attr}' in the form: '{self.form_model.__dict__.keys()}",
                )

    def test_create(self):
        self.assertIsInstance(self.form_model, Form)
        self.assertEqual(self.form_model.category, FormCategory.MODEL)

        self.assertIsInstance(self.form_model_2, Form)
        self.assertEqual(self.form_model_2.category, FormCategory.MODEL)

        self.assertIsInstance(self.form_instance, Form)
        self.assertEqual(self.form_instance.category, FormCategory.INSTANCE)


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
        self.test_form_instance = self.form_model.instantiate(name="___test form from 1st")

        self.assertTrue(self.test_form_instance.model_id, self.form_model.id)

    def test_model_form_instantiation_from_client(self):
        self.test_form_instance = self.client.instantiate_form(name="___TEST_FORM_INSTANCE")



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

    def test_form_retrieve_by_name_from_scope(self):
        form = self.project.form(name=self.form_model_name)

        self.assertIsInstance(form, Form)

    def test_forms_retrieve_by_context_from_scope(self):
        forms = self.project.forms(context=[self.asset_context])

        self.assertEqual(len(forms), 2)
        for form in forms:
            self.assertIsInstance(form, Form)
        self.assertIn(self.form_model.id, [form.id for form in forms])
        self.assertIn(self.form_model_2.id, [form.id for form in forms])

    def test_forms_retrieve_instances_by_model_from_scope(self):
        form_instances = self.project.forms(model=self.form_model, category=FormCategory.INSTANCE)

        self.assertTrue(len(form_instances) == 1)
        form_instance = form_instances[0]

        self.assertTrue(form_instance.category, FormCategory.INSTANCE)
        self.assertTrue(form_instance.model_id, self.form_model.id)
