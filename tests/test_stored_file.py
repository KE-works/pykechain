import os

from pykechain.enums import StoredFileClassification
from tests.classes import TestBetamax


class TestStoredFiles(TestBetamax):
    def setUp(self):
        super().setUp()
        self.test_assets_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
        )
        self.upload_path = os.path.join(
            self.test_assets_dir,
            "tests",
            "files",
            "test_upload_image_to_attachment_property",
            "test_upload_image.png",
        )
        self.stored_file = self.client.create_stored_file(
            name="__TEST_STORED_FILE",
            scope=self.project,
            classification=StoredFileClassification.SCOPED,
            filepath=self.upload_path,
            description="__TEST_STORED_FILE_DESCRIPTION"
        )

    def tearDown(self):
        if self.stored_file:
            self.stored_file.delete()
        super().tearDown()

    def test_add_stored_file(self):
        print()
