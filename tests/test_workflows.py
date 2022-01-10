import pytest as pytest

from pykechain.enums import WorkflowCategory
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
            category=WorkflowCategory.CATALOG,
            scope=self.project
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

        workflow = self.client.workflow("Simple Workflow", category=WorkflowCategory.CATALOG, scope=self.project)
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
