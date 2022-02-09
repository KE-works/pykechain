from copy import deepcopy
from random import shuffle
from unittest import skip

from pykechain.enums import StatusCategory, TransitionType, WorkflowCategory
from pykechain.exceptions import NotFoundError
from pykechain.models.input_checks import check_list_of_base
from pykechain.models.workflow import Status, Workflow
from tests.classes import TestBetamax


class TestWorkflows(TestBetamax):
    """
    Test retrieval and scope attributes and methods.
    """

    def setUp(self):
        super().setUp()
        self.workflow: Workflow = self.client.workflow(
            "Simple Workflow", category=WorkflowCategory.CATALOG
        )

    def tearDown(self):
        super().tearDown()

    def test_workflow_attributes(self):
        attributes = [
            "id",
            "name",
            "description",
            "ref",
            "derived_from_id",
            "created_at",
            "updated_at",
            "category",
            "scope_id",
            "statuses",
            "transitions",
            "options",
            "active",
        ]

        workflow = self.client.workflow(
            "Simple Workflow", category=WorkflowCategory.CATALOG
        )
        for attr in attributes:
            with self.subTest(attr):
                self.assertTrue(
                    hasattr(workflow, attr),
                    f"Could not find '{attr}' in the workflow: '{workflow.__dict__.keys()}",
                )

    def test_single_workflow_retrieve_on_pk(self):
        workflow_id = self.workflow.id

        retr_on_id = self.client.workflow(pk=workflow_id)
        pass

    def test_clone_workflow_to_scope(self):
        """Testing the 'import workflow'."""
        catalog_workflow = self.client.workflow(
            name="Simple Workflow", category=WorkflowCategory.CATALOG
        )

        imported_workflow = catalog_workflow.clone(
            target_scope=self.project, name="___Imported Simple Workflow"
        )

        self.assertTrue(imported_workflow)
        retrieved_imported_workflow = self.client.workflow(
            name="___Imported Simple Workflow", scope=self.project
        )
        self.assertEqual(imported_workflow.id, retrieved_imported_workflow.id)

        retrieved_imported_workflow.delete()

    def test_import_workflow_in_a_scope_with_import_workflow_method_on_scope(self):
        """Test the create of a new workflow in a scope."""
        imported_workflow = self.project.import_workflow(
            workflow=self.workflow, name="___Imported Simple Flow"
        )
        self.assertEqual(imported_workflow.derived_from_id, self.workflow.id)
        imported_workflow.delete()

    def test_clone_workflow_in_a_scope_in_the_same_scope(self):
        test_wf = self.project.import_workflow(workflow=self.workflow, name="__TEST")

        cloned_wf = test_wf.clone(
            target_scope=test_wf.scope_id, name="CLONED WITHIN THE SOCPE"
        )
        self.assertTrue(cloned_wf)
        self.assertEqual(cloned_wf.derived_from_id, test_wf.id)

        # teardown
        test_wf.delete()
        cloned_wf.delete()


class TestWorkflowMethods(TestBetamax):
    def setUp(self):
        super().setUp()
        self.catalog_workflow: Workflow = self.client.workflow(
            "Simple Workflow", category=WorkflowCategory.CATALOG
        )
        self.workflow = self.project.import_workflow(
            workflow=self.catalog_workflow,
            name="__TEST Imported Simple Flow from Catalog",
        )

    def tearDown(self):
        super().tearDown()
        try:
            self.workflow.delete()
        except NotFoundError:
            # we pass this silently as workflow delete when the
            # casettes are irrelevant and returns a 404 NotFoundError
            pass

    def test_workflow_in_and_activate(self):
        self.workflow.deactivate()
        self.assertFalse(self.workflow.active)
        self.workflow.activate()
        self.assertTrue(self.workflow.active)

    def test_create_delete_status_and_create_delete_workflow_transition(self):
        """Test to create a transition on a workflow.

        - tests creation of status on workflow
        - tests deletion of status
        - tests deletion of transition on workflow
        """

        count_transitions = len(self.workflow.transitions)
        test_status = self.workflow.create_status(
            name="__TEST DONE", category=StatusCategory.DONE
        )
        test_transition = self.workflow.transition(test_status.name)
        self.workflow.delete_transition(test_transition)
        from_status = self.workflow.create_status(
            name="__TEST FROM", category=StatusCategory.TODO
        )
        from_transition = self.workflow.transition(from_status.name)
        self.workflow.delete_transition(from_transition)

        new_transition = self.workflow.create_transition(
            name="___test transition",
            to_status=test_status,
            transition_type=TransitionType.DIRECTED,
            from_status=[from_status],
        )

        self.workflow.delete_transition(new_transition)
        test_status.delete()
        from_status.delete()

    def test_workflow_status_order(self):
        cloned_wf = self.workflow.clone(
            name="___cloned_workflow_status_order", target_scope=self.workflow.scope_id
        )

        try:
            status_ids = [s.id for s in deepcopy(cloned_wf.statuses)]
            reversed_status_ids = list(reversed(status_ids))

            cloned_wf.status_order = reversed_status_ids

            self.assertListEqual(
                reversed_status_ids, check_list_of_base(cloned_wf.status_order, Status)
            )
        finally:
            cloned_wf.delete()

    def test_workflow_unlink_and_link_transitions(self):
        transitions = deepcopy(self.workflow.transitions)
        the_transition_to_unlink = transitions[-1]

        # unlink
        self.workflow.unlink_transitions([the_transition_to_unlink])
        self.assertListEqual(self.workflow.transitions, transitions[:-1])

        # relink
        self.workflow.link_transitions([the_transition_to_unlink])
        self.assertListEqual(self.workflow.transitions, transitions)
