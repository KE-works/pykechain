import os

from pykechain.enums import StoredFileCategory, StoredFileClassification
from pykechain.exceptions import NotFoundError
from pykechain.models.stored_file import StoredFile
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
        self.name = "__TEST_STORED_FILE"
        self.stored_file = self.client.create_stored_file(
            name=self.name,
            scope=self.project,
            classification=StoredFileClassification.SCOPED,
            filepath=self.upload_path,
            description="__TEST_STORED_FILE_DESCRIPTION",
        )
        self.added_stored_file = None

    def tearDown(self):
        if self.stored_file:
            self.stored_file.delete()
        if self.added_stored_file:
            self.added_stored_file.delete()
        super().tearDown()

    def test_add_stored_file(self):
        name = "__TEST_ADD_STORED_FILE"
        self.client.create_stored_file(
            name=name,
            scope=self.project,
            category=StoredFileCategory.REFERENCED,
            classification=StoredFileClassification.SCOPED,
            filepath=self.upload_path,
        )

        self.added_stored_file = self.client.stored_file(name=name)
        self.assertEqual(self.added_stored_file.category, StoredFileCategory.REFERENCED)
        self.assertEqual(
            self.added_stored_file.classification, StoredFileClassification.SCOPED
        )
        self.assertIsInstance(self.added_stored_file, StoredFile)

    def test_retrieve_stored_file(self):
        existing_file = self.client.stored_file(
            classification=StoredFileClassification.SCOPED
        )

        self.assertEqual(existing_file.category, StoredFileCategory.GLOBAL)
        self.assertEqual(existing_file.name, self.name)
        self.assertIsInstance(existing_file, StoredFile)

    def test_retrieve_stored_files(self):
        existing_files = self.client.stored_files(
            classification=StoredFileClassification.SCOPED
        )

        self.assertEqual(len(existing_files), 1)
        self.assertEqual(
            existing_files[0].classification, StoredFileClassification.SCOPED
        )
        self.assertEqual(existing_files[0].category, StoredFileCategory.GLOBAL)
        self.assertEqual(existing_files[0].name, self.name)
        self.assertIsInstance(existing_files[0], StoredFile)

    def test_delete_stored_file(self):
        self.assertIsInstance(self.client.stored_file(name=self.name), StoredFile)

        self.stored_file.delete()

        with self.assertRaises(NotFoundError):
            self.client.stored_file(name=self.name)

        self.stored_file = None

    def test_edit_name_stored_file(self):
        self.stored_file.edit(name="__TEST_EDIT_NAME")

        self.assertEqual(self.stored_file.name, "__TEST_EDIT_NAME")

    def test_edit_stored_file_attributes(self):
        self.stored_file.edit(
            description="__TEST_EDIT_DESCRIPTION",
            classification=StoredFileClassification.GLOBAL,
            category=StoredFileCategory.REFERENCED,
            scope=None,
        )
        self.assertEqual(
            self.stored_file.classification, StoredFileClassification.GLOBAL
        )
        self.assertEqual(self.stored_file.category, StoredFileCategory.REFERENCED)
        self.assertEqual(self.stored_file.scope, None)
