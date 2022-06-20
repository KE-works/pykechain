import uuid

import jsonschema

from pykechain.enums import (
    FormCategory,
    Multiplicity,
    PropertyType,
    StatusCategory,
    WorkflowCategory,
)
from pykechain.exceptions import (
    APIError,
    ForbiddenError,
    IllegalArgumentError,
    NotFoundError,
)
from pykechain.models.form import Form
from tests.classes import TestBetamax


class TestForms(TestBetamax):
    """
    Test retrieval and forms attributes and methods.
    """

    def setUp(self):
        super().setUp()
        self.cross_scope_project = self.client.scope(ref="cannondale-project")
        self.workflow = self.client.workflow(
            name="Simple Form Flow", category=WorkflowCategory.CATALOG
        )
        self.discipline_context = self.project.context(name="Discipline 1")
        self.asset_context = self.project.context(name="Object 1")
        self.form_model_name = "__TEST__FORM_MODEL"
        self.form_model_name_2 = "__TEST__FORM_MODEL_2"

        self.form_model = self.client.create_form_model(
            name=self.form_model_name,
            scope=self.project,
            workflow=self.workflow,
            category=FormCategory.MODEL,
            contexts=[self.asset_context, self.discipline_context],
        )
        self.form_model_2 = self.project.create_form_model(
            name=self.form_model_name_2,
            workflow=self.workflow,
            category=FormCategory.MODEL,
            contexts=[self.asset_context],
        )
        self.form_instance = self.form_model.instantiate(name="__TEST_FORM_INSTANCE")
        self.test_form_instance = None
        self.cloned_form_model = None
        self.form_model_for_deletion = None
        self.cloned_workflow = None

    def tearDown(self):
        super().tearDown()
        if self.form_instance:
            try:
                self.form_instance.delete()
            except (NotFoundError, APIError):
                pass
        if self.test_form_instance:
            try:
                self.test_form_instance.delete()
            except (NotFoundError, APIError):
                pass
        if self.form_model:
            try:
                self.form_model.delete()
            except (NotFoundError, APIError):
                pass
        if self.form_model_2:
            try:
                self.form_model_2.delete()
            except (NotFoundError, APIError):
                pass
        if self.form_model_for_deletion:
            try:
                self.form_model_for_deletion.delete()
            except (NotFoundError, APIError):
                pass
        if self.cloned_form_model:
            try:
                self.cloned_form_model.delete()
            except (NotFoundError, APIError):
                pass
        if self.cloned_workflow:
            try:
                self.cloned_workflow.delete()
            except (NotFoundError, APIError):
                pass

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
            form_instance = self.form_model.instances()[0]
            self.assertTrue(form_instance.category, FormCategory.INSTANCE)
            self.assertTrue(form_instance.model_id, self.form_model.id)

    def test_model_form_instantiation(self):
        self.test_form_instance = self.form_model.instantiate(
            name="__TEST_FORM_INSTANCE"
        )

        self.assertTrue(self.test_form_instance.model_id, self.form_model.id)

    def test_model_form_instantiation_from_client(self):
        self.test_form_instance = self.client.instantiate_form(
            name="___TEST_FORM_INSTANCE", model=self.form_model
        )
        self.assertIsInstance(self.test_form_instance, Form)
        self.assertEqual(self.test_form_instance.category, FormCategory.INSTANCE)
        self.assertTrue(self.test_form_instance.model_id, self.form_model.id)

    def test_model_form_instantiation_from_scope(self):
        self.test_form_instance = self.project.instantiate_form(
            name="___TEST_FORM_INSTANCE", model=self.form_model
        )
        self.assertIsInstance(self.test_form_instance, Form)
        self.assertEqual(self.test_form_instance.category, FormCategory.INSTANCE)
        self.assertTrue(self.test_form_instance.model_id, self.form_model.id)

    def test_model_form_instantiation_from_wrong_scope(self):
        with self.assertRaises(IllegalArgumentError):
            self.test_form_instance = self.cross_scope_project.instantiate_form(
                name="___TEST_FORM_INSTANCE", model=self.form_model
            )

    def test_model_clone_same_scope(self):
        self.cloned_form_model = self.form_model.clone(
            name="__TEST_FORM_MODEL_CLONE",
            target_scope=self.project,
            contexts=[self.asset_context, self.discipline_context],
        )
        self.assertTrue(self.cloned_form_model)
        self.assertIsInstance(self.cloned_form_model, Form)
        self.assertEqual(self.form_model.scope_id, self.cloned_form_model.scope_id)
        self.assertIn(
            self.asset_context.id,
            [
                context["id"]
                for context in self.cloned_form_model._json_data["contexts"]
            ],
        )
        self.assertIn(
            self.discipline_context.id,
            [
                context["id"]
                for context in self.cloned_form_model._json_data["contexts"]
            ],
        )

    def test_model_clone_no_target_scope(self):
        self.cloned_form_model = self.form_model.clone(
            name="__TEST_FORM_MODEL_CLONE",
            contexts=[self.asset_context, self.discipline_context],
        )
        self.assertTrue(self.cloned_form_model)
        self.assertIsInstance(self.cloned_form_model, Form)
        self.assertEqual(self.form_model.scope_id, self.cloned_form_model.scope_id)
        self.assertIn(
            self.asset_context.id,
            [
                context["id"]
                for context in self.cloned_form_model._json_data["contexts"]
            ],
        )
        self.assertIn(
            self.discipline_context.id,
            [
                context["id"]
                for context in self.cloned_form_model._json_data["contexts"]
            ],
        )

    def test_model_clone_cross_scope(self):
        self.cloned_form_model = self.form_model.clone(
            name="__TEST_FORM_MODEL_CLONE_CROSS_SCOPE",
            target_scope=self.cross_scope_project,
            contexts=[self.asset_context, self.discipline_context],
        )
        self.assertTrue(self.cloned_form_model)
        self.assertIsInstance(self.cloned_form_model, Form)
        self.assertEqual(self.cross_scope_project.id, self.cloned_form_model.scope_id)
        self.assertIn(
            self.asset_context.name,
            [
                context["name"]
                for context in self.cloned_form_model._json_data["contexts"]
            ],
        )
        self.assertIn(
            self.discipline_context.name,
            [
                context["name"]
                for context in self.cloned_form_model._json_data["contexts"]
            ],
        )

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
        form_instances = self.project.forms(
            model=self.form_model, category=FormCategory.INSTANCE
        )

        self.assertTrue(len(form_instances) == 1)
        form_instance = form_instances[0]

        self.assertTrue(form_instance.category, FormCategory.INSTANCE)
        self.assertTrue(form_instance.model_id, self.form_model.id)

    def test_form_model_edit(self):
        new_name = "__TEST_EDITED_FORM_MODEL"
        self.form_model_2.edit(name=new_name)
        self.assertEqual(self.form_model_2.name, new_name)

    def test_form_model_edit_with_instances(self):
        new_name = "__TEST_EDITED_FORM_MODEL"
        self.form_model.edit(name=new_name)
        self.assertEqual(self.form_model.name, new_name)

    def test_form_instance_edit(self):
        new_name = "__TEST_INSTANCE_EDITED"
        self.form_instance.edit(name=new_name)
        self.assertEqual(self.form_instance.name, new_name)

    def test_forms_delete(self):
        form_model_name = "__TEST_FORM_MODEL_FOR_DELETION"
        self.form_model_for_deletion = self.client.create_form_model(
            name=form_model_name,
            scope=self.project,
            workflow=self.workflow,
            category=FormCategory.MODEL,
            contexts=[self.asset_context, self.discipline_context],
        )
        self.assertIsInstance(self.form_model_for_deletion, Form)
        self.form_model_for_deletion.delete()
        with self.assertRaises(APIError, msg="Cant delete the same Form twice!"):
            self.form_model_for_deletion.delete()
        with self.assertRaises(NotFoundError, msg="Deleted Form cannot be found!"):
            self.project.form(name=form_model_name)

    def test_form_has_part_is_true(self):
        part_model = self.project.model(name=self.form_model.name)
        has_part_check = self.form_model.has_part(part=part_model)
        self.assertTrue(has_part_check)

        part_instance = part_model.instance()
        has_part_check = self.form_instance.has_part(part=part_instance)
        self.assertTrue(has_part_check)

    def test_form_has_part_is_false(self):
        part_model = self.project.model(name="Bike")

        has_part_check = self.form_model.has_part(part=part_model)
        self.assertFalse(has_part_check)

    def test_form_has_part_wrong_inputs(self):
        with self.assertRaises(IllegalArgumentError):
            self.form_model.has_part(part=self.discipline_context)

    def test_form_workflow_compatible_within_scope(self):
        workflows = self.form_model.workflows_compatible_with_scope(scope=self.project)
        self.assertEqual(len(workflows), 1)
        self.cloned_workflow = self.workflow.clone(
            target_scope=self.project, name="CLONED WORKFLOW"
        )
        workflows = self.form_model.workflows_compatible_with_scope(scope=self.project)
        self.assertEqual(len(workflows), 2)

    def test_form_workflow_compatible_within_scope_wrong_inputs(self):
        with self.assertRaises(IllegalArgumentError):
            self.form_model.workflows_compatible_with_scope(
                scope=self.discipline_context
            )


class TestFormsBulk(TestBetamax):
    """
    Test bulk forms attributes and methods.
    """

    def setUp(self):
        super().setUp()
        self.workflow = self.client.workflow(
            name="Simple Form Flow", category=WorkflowCategory.CATALOG
        )
        self.discipline_context = self.project.context(name="Discipline 1")
        self.asset_context = self.project.context(name="Object 1")
        self.form_model_name = "__TEST__FORM_MODEL"
        self.form_model = self.client.create_form_model(
            name=self.form_model_name,
            scope=self.project,
            workflow=self.workflow,
            category=FormCategory.MODEL,
            contexts=[self.asset_context, self.discipline_context],
        )
        self.new_forms = list()
        for idx in range(1, 5):
            form_dict = {
                "form": self.form_model,
                "values": {
                    "name": f"Form {idx}",
                    "contexts": [self.asset_context],
                },
            }
            self.new_forms.append(form_dict)
        self.forms_created = None

    def tearDown(self):
        super().tearDown()
        if self.forms_created:
            for form in self.forms_created:
                try:
                    form.delete()
                except APIError:
                    pass
        if self.form_model:
            try:
                self.form_model.delete()
            except (ForbiddenError, APIError):
                pass

    def test_bulk_instantiate_forms(self):
        self.forms_created = self.client._create_forms_bulk(
            forms=self.new_forms, retrieve_instances=True
        )
        for form in self.forms_created:
            self.assertIsInstance(form, Form)
            self.assertEqual(form.category, FormCategory.INSTANCE)
            self.assertEqual(form.model_id, self.form_model.id)

    def test_bulk_delete_forms(self):
        self.forms_created = self.client._create_forms_bulk(
            forms=self.new_forms, retrieve_instances=True
        )
        input_forms_and_uuids = [
            self.forms_created[0],
            self.forms_created[1],
            self.forms_created[2].id,
            self.forms_created[3].id,
        ]
        self.client._delete_forms_bulk(forms=input_forms_and_uuids)
        for idx in range(1, 5):
            with self.subTest(idx=idx):
                with self.assertRaises(NotFoundError):
                    self.project.form(name=f"Form {idx}")

    def test_bulk_delete_forms_with_wrong_input(self):
        wrong_input = [self.project.activity(name="Specify wheel diameter")]
        with self.assertRaises(IllegalArgumentError):
            self.client._delete_forms_bulk(forms=wrong_input)


class TestFormsMethods(TestBetamax):
    """
    Test linking and unlinking contexts to forms.
    """

    def setUp(self):
        super().setUp()
        self.workflow = self.client.workflow(
            name="Simple Form Flow", category=WorkflowCategory.CATALOG
        )
        self.discipline_context = self.project.context(name="Discipline 1")
        self.asset_context = self.project.context(name="Object 1")
        self.location_context = self.project.context(name="Location 1")
        self.form_model_name = "__TEST__FORM_MODEL"
        self.form_model = self.client.create_form_model(
            name=self.form_model_name,
            scope=self.project,
            workflow=self.workflow,
            category=FormCategory.MODEL,
            contexts=[self.asset_context],
        )
        self.form_instance_to_link = self.form_model.instantiate(
            name="__TEST_FORM_INSTANCE_LINK"
        )
        self.form_instance_to_unlink = self.form_model.instantiate(
            name="__TEST_FORM_INSTANCE_UNLINK",
            contexts=[
                self.asset_context,
                self.discipline_context,
                self.location_context,
            ],
        )
        self.form_instance_to_set_assignees = self.form_model.instantiate(
            name="__TEST_FORM_INSTANCE_SET_STATUS_ASSIGNEES"
        )
        self.form_instance_to_transition = self.form_model.instantiate(
            name="__TEST_FORM_INSTANCE_APPLY_TRANSITION"
        )

    def tearDown(self):
        super().tearDown()
        if self.form_instance_to_link:
            try:
                self.form_instance_to_link.delete()
            except (ForbiddenError, APIError):
                pass
        if self.form_instance_to_unlink:
            try:
                self.form_instance_to_unlink.delete()
            except (ForbiddenError, APIError):
                pass
        if self.form_instance_to_set_assignees:
            try:
                self.form_instance_to_set_assignees.delete()
            except (ForbiddenError, APIError):
                pass
        if self.form_instance_to_transition:
            try:
                self.form_instance_to_transition.delete()
            except (ForbiddenError, APIError):
                pass
        if self.form_model:
            try:
                self.form_model.delete()
            except (ForbiddenError, APIError):
                pass

    def test_link_contexts_to_form_model(self):
        self.form_model.link_contexts(
            contexts=[self.discipline_context, self.location_context]
        )
        self.assertIn(
            self.asset_context.id,
            [context["id"] for context in self.form_model._json_data["contexts"]],
        )
        self.assertIn(
            self.discipline_context.id,
            [context["id"] for context in self.form_model._json_data["contexts"]],
        )
        self.assertIn(
            self.location_context.id,
            [context["id"] for context in self.form_model._json_data["contexts"]],
        )
        self.assertEqual(len(self.form_model._json_data["contexts"]), 3)

    def test_link_contexts_to_form_instance(self):
        self.form_instance_to_link.link_contexts(contexts=[self.location_context])
        self.assertIn(
            self.location_context.id,
            [
                context["id"]
                for context in self.form_instance_to_link._json_data["contexts"]
            ],
        )
        self.assertEqual(len(self.form_instance_to_link._json_data["contexts"]), 1)

    def test_unlink_contexts_to_form_model(self):
        self.form_model.unlink_contexts(contexts=[self.asset_context])
        self.assertEqual(len(self.form_model._json_data["contexts"]), 0)

    def test_unlink_contexts_to_form_instance(self):
        self.form_instance_to_unlink.unlink_contexts(
            contexts=[self.location_context, self.asset_context]
        )
        self.assertIn(
            self.discipline_context.id,
            [
                context["id"]
                for context in self.form_instance_to_unlink._json_data["contexts"]
            ],
        )
        self.assertEqual(len(self.form_instance_to_unlink._json_data["contexts"]), 1)

    def test_unlink_non_connected_contexts_from_form(self):
        with self.assertRaises(APIError):
            self.form_model.unlink_contexts(
                contexts=[self.discipline_context, self.asset_context]
            )

    def test_set_status_assignees(self):
        status_assignees_list = list()
        test_manager = self.client.user("testmanager")
        supervisor = self.client.user("supervisor")
        test_lead = self.client.user("testlead")
        for status_form in self.form_instance_to_set_assignees.status_forms:
            status_dict = {
                "status": status_form.status,
                "assignees": [test_manager, supervisor, test_lead],
            }
            status_assignees_list.append(status_dict)
        self.form_instance_to_set_assignees.set_status_assignees(
            statuses=status_assignees_list
        )
        for status_form in self.form_instance_to_set_assignees._status_assignees:
            self.assertIn(
                test_manager.id,
                [status_assignee["id"] for status_assignee in status_form["assignees"]],
            )
            self.assertEqual(len(status_form["assignees"]), 3)

    def test_set_status_assignees_with_wrong_format(self):
        status_assignees_list = list()
        test_manager = self.client.user("testmanager")
        for status_form in self.form_instance_to_set_assignees.status_forms:
            status_dict = {"id": status_form.status, "assignees": [test_manager]}
            status_assignees_list.append(status_dict)
        with self.assertRaises(IllegalArgumentError):
            self.form_instance_to_set_assignees.set_status_assignees(
                statuses=status_assignees_list
            )

    def test_set_status_assignees_with_wrong_input(self):
        status_assignees_list = list()
        test_manager = self.client.user("testmanager")
        for status_form in self.form_instance_to_set_assignees.status_forms:
            status_dict = {
                "status": status_form.id,  # This should be status_form.status
                "assignees": [test_manager],
            }
            status_assignees_list.append(status_dict)
        with self.assertRaises(APIError):
            self.form_instance_to_set_assignees.set_status_assignees(
                statuses=status_assignees_list
            )

    def test_apply_transition(self):
        in_progress_transition = self.workflow.transition("In progress")
        done_transition = self.workflow.transition("Done")
        self.assertEqual(
            self.form_instance_to_transition.active_status["status_category"],
            StatusCategory.TODO,
        )
        self.form_instance_to_transition.apply_transition(
            transition=in_progress_transition
        )
        self.assertEqual(
            self.form_instance_to_transition.active_status["status_category"],
            StatusCategory.INPROGRESS,
        )
        self.form_instance_to_transition.apply_transition(transition=done_transition)
        self.assertEqual(
            self.form_instance_to_transition.active_status["status_category"],
            StatusCategory.DONE,
        )

    def test_apply_transition_with_wrong_input(self):
        with self.assertRaises(IllegalArgumentError):
            self.form_instance_to_transition.apply_transition(transition=self.workflow)

    def test_retrieve_possible_transitions(self):
        possible_transitions = self.form_instance_to_transition.possible_transitions()
        for transition in possible_transitions:
            self.assertIn(transition.id, [t.id for t in self.workflow.transitions])
        self.assertEqual(len(possible_transitions), 5)


class TestFormsPreFillPartMethods(TestBetamax):
    """
    Test linking and unlinking contexts to forms.
    """

    def setUp(self):
        super().setUp()
        self.workflow = self.client.workflow(
            name="Simple Form Flow", category=WorkflowCategory.CATALOG
        )
        self.form_model_name = "__TEST__FORM_MODEL"
        self.form_model = self.client.create_form_model(
            name=self.form_model_name,
            scope=self.project,
            workflow=self.workflow,
            category=FormCategory.MODEL,
            contexts=[],
        )
        self.form_model_root = self.form_model.form_model_root
        self.a_part_model = self.client.create_model(
            parent=self.form_model_root,
            name="A Part Model",
            multiplicity=Multiplicity.ZERO_MANY,
        )
        self.p1 = self.client.create_property(
            model=self.a_part_model, name="p1", property_type=PropertyType.CHAR_VALUE
        )

    def tearDown(self):
        super().tearDown()
        if self.form_model:
            try:
                self.form_model.delete()
            except (ForbiddenError, APIError):
                pass

    def test_form_prefill_parts_can_be_set(self):
        prefill_parts = {
            self.a_part_model.id: [
                dict(
                    name="1st instance",
                    part_properties=[dict(property_id=self.p1.id, value=1)],
                ),
                dict(
                    name="2nd instance",
                    part_properties=[dict(property_id=self.p1.id, value=2)]
                )
            ]
        }

        self.assertDictEqual(self.form_model._prefill_parts, {})
        self.form_model.set_prefill_parts(prefill_parts=prefill_parts)
        self.assertDictEqual(prefill_parts, self.form_model._prefill_parts)

    def test_form_prefill_parts_with_wrong_payload(self):
        prefill_parts = {"foo": "bar"}
        self.assertDictEqual(self.form_model._prefill_parts, {})
        with self.assertRaisesRegex(jsonschema.ValidationError, "'foo' does not match"):
            self.form_model.set_prefill_parts(prefill_parts=prefill_parts)

        prefill_parts = {str(uuid.uuid4()): ["bar"]}
        self.assertDictEqual(self.form_model._prefill_parts, {})
        with self.assertRaisesRegex(jsonschema.ValidationError, "'bar' is not of type 'object'"):
            self.form_model.set_prefill_parts(prefill_parts=prefill_parts)

        prefill_parts = {str(uuid.uuid4()): [{"name": "bar"}]}
        self.assertDictEqual(self.form_model._prefill_parts, {})
        with self.assertRaisesRegex(jsonschema.ValidationError, "'part_properties' is a required property"):
            self.form_model.set_prefill_parts(prefill_parts=prefill_parts)

        prefill_parts = {str(uuid.uuid4()): [{"name": "bar", "part_properties": {}}]}
        self.assertDictEqual(self.form_model._prefill_parts, {})
        with self.assertRaisesRegex(jsonschema.ValidationError, "{} is not of type 'array'"):
            self.form_model.set_prefill_parts(prefill_parts=prefill_parts)
