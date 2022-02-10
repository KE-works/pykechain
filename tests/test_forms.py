import pytest

from pykechain.enums import FormCategory, WorkflowCategory
from pykechain.exceptions import APIError, IllegalArgumentError, NotFoundError
from pykechain.models.form import Form
from tests.classes import TestBetamax


@pytest.mark.skipif(
    "os.getenv('GITHUB_ACTIONS', False)",
    reason="Skipping tests when using Travis or Github Actions "
           "as there is no public forms world yet",
)
class TestForms(TestBetamax):
    """
    Test retrieval and forms attributes and methods.
    """

    def setUp(self):
        super().setUp()
        self.cross_scope_project = self.client.scope(ref="cannondale-project")
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
        self.test_form_instance = None
        self.cloned_form_model = None
        self.form_model_for_deletion = None

    def tearDown(self):
        super().tearDown()
        if self.form_instance:
            self.form_instance.delete()
        if self.test_form_instance:
            self.test_form_instance.delete()
        if self.form_model:
            self.form_model.delete()
        if self.form_model_2:
            self.form_model_2.delete()
        if self.form_model_for_deletion:
            try:
                self.form_model_for_deletion.delete()
            except APIError:
                pass
        if self. cloned_form_model:
            self.cloned_form_model.delete()

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
        self.test_form_instance = self.form_model.instantiate(name="__TEST_FORM_INSTANCE")

        self.assertTrue(self.test_form_instance.model_id, self.form_model.id)

    def test_model_form_instantiation_from_client(self):
        self.test_form_instance = self.client.instantiate_form(name="___TEST_FORM_INSTANCE",
                                                               model=self.form_model)
        self.assertIsInstance(self.test_form_instance, Form)
        self.assertEqual(self.test_form_instance.category, FormCategory.INSTANCE)
        self.assertTrue(self.test_form_instance.model_id, self.form_model.id)

    def test_model_form_instantiation_from_scope(self):
        self.test_form_instance = self.project.instantiate_form(name="___TEST_FORM_INSTANCE",
                                                                model=self.form_model)
        self.assertIsInstance(self.test_form_instance, Form)
        self.assertEqual(self.test_form_instance.category, FormCategory.INSTANCE)
        self.assertTrue(self.test_form_instance.model_id, self.form_model.id)

    def test_model_form_instantiation_from_wrong_scope(self):
        with self.assertRaises(IllegalArgumentError):
            self.test_form_instance = self.cross_scope_project.instantiate_form(
                name="___TEST_FORM_INSTANCE",
                model=self.form_model
            )

    def test_model_form_delete(self):
        form_instance = self.form_model.instantiate(name="___test form from 1st")
        self.assertTrue(form_instance.model_id, self.form_model.id)

        # delete
        form_instance.delete()
        with self.assertRaisesRegex(NotFoundError, "Could not reload Form"):
            form_instance.refresh()

    def test_model_clone(self):
        self.cloned_form_model = self.form_model.clone(name="__TEST_FORM_MODEL_CLONE",
                                                       target_scope=self.project)
        self.assertTrue(self.cloned_form_model)
        self.assertIsInstance(self.cloned_form_model, Form)
        self.assertIn(self.asset_context.id,
                      [context['id'] for context in self.cloned_form_model._json_data['contexts']])
        self.assertIn(self.discipline_context.id,
                      [context['id'] for context in self.cloned_form_model._json_data['contexts']])

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

    # def test_forms_edit(self):
    #     new_name = "__TEST_EDITED_FORM_MODEL"
    #     self.form_model.edit(name=new_nam)
    def test_forms_delete(self):
        form_model_name = "__TEST_FORM_MODEL_FOR_DELETION"
        self.form_model_for_deletion = self.client.create_form_model(
            name=form_model_name,
            scope=self.project,
            workflow=self.workflow,
            category=FormCategory.MODEL,
            contexts=[self.asset_context, self.discipline_context])
        self.assertIsInstance(self.form_model_for_deletion, Form)
        self.form_model_for_deletion.delete()
        with self.assertRaises(APIError, msg="Cant delete the same Form twice!"):
            self.form_model_for_deletion.delete()
        with self.assertRaises(NotFoundError, msg="Deleted Form cannot be found!"):
            self.project.form(name=form_model_name)


class TestBulkForms(TestBetamax):
    """
    Test bulk forms attributes and methods.
    """
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_bulk_delete_parts(self):
        input_parts_and_uuids = [
            self.parts_created[0],
            self.parts_created[1],
            self.parts_created[2].id,
            self.parts_created[3].id,
        ]
        self.client._delete_parts_bulk(parts=input_parts_and_uuids)
        for idx in range(1, 5):
            with self.subTest(idx=idx):
                with self.assertRaises(NotFoundError):
                    self.project.part(name=f"Wheel {idx}")

    def test_bulk_delete_parts_with_wrong_input(self):
        wrong_input = [self.project.activity(name="Specify wheel diameter")]
        with self.assertRaises(IllegalArgumentError):
            self.client._delete_parts_bulk(parts=wrong_input)

