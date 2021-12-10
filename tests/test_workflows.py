import pytest

from pykechain.enums import WorkflowCategory
from pykechain.exceptions import NotFoundError
from pykechain.models.workflow import Workflow
from tests.classes import TestBetamax


@pytest.mark.skipif(
    "os.getenv('GITHUB_ACTIONS', False)",
    reason="Skipping tests when using Travis or Github Actions "
           "as there is no public workflows world yet",
)
class TestWorkflows(TestBetamax):
    """
    Test retrieval and scope attributes and methods.
    """

    def setUp(self):
        super().setUp()
        self.workflow: Workflow = self.client.workflow(
            "Simple Workflow",
            category=WorkflowCategory.CATALOG
        )

    def tearDown(self):
        super().tearDown()

    def test_workflow_attributes(self):
        attributes = [
            "id",
            "name",
            "description",
            "ref",
            "derived_from_id",  # derived_from on the serializer
            "created_at",
            "updated_at",
            "category",
            "scope_id",
            "statuses",
            "_transitions",
            "options",
            "active",
        ]

        workflow = self.client.workflow("Simple Workflow", category=WorkflowCategory.CATALOG)
        for attr in attributes:
            with self.subTest(attr):
                self.assertTrue(
                    hasattr(workflow, attr),
                    f"Could not find '{attr}' in the workflow: '{workflow.__dict__.keys()}",
                )

    def test_workflow_instances(self):
        with self.subTest("testing instances"):
            workflow_instances = self.workflow_model.instances()
            self.assertTrue(len(workflow_instances) >= 1)
            workflow_instance = workflow_instances[0]

            self.assertTrue(workflow_instance.category, WorkflowCategory.INSTANCE)
            self.assertTrue(workflow_instance.model_id, self.workflow_model.id)

        with self.subTest("testing instance"):
            workflow_instance = self.workflow_model.instance()
            self.assertTrue(workflow_instance.category, WorkflowCategory.INSTANCE)
            self.assertTrue(workflow_instance.model_id, self.workflow_model.id)

    def test_model_workflow_instantiation(self):
        workflow_instance = self.workflow_model.instantiate(name="___test workflow from 1st")

        self.assertTrue(workflow_instance.model_id, self.workflow_model.id)

        # delete
        workflow_instance.delete()

    def test_model_workflow_delete(self):
        workflow_instance = self.workflow_model.instantiate(name="___test workflow from 1st")
        self.assertTrue(workflow_instance.model_id, self.workflow_model.id)

        # delete
        workflow_instance.delete()
        with self.assertRaisesRegex(NotFoundError, "Could not reload Workflow"):
            workflow_instance.refresh()

    def test_model_clone(self):
        cloned_workflow_model = self.workflow_model.clone(name="___ test clone workflow 1st",
                                                          target_scope=self.project)
        self.assertTrue(cloned_workflow_model)

        # delete
        cloned_workflow_model.delete()
