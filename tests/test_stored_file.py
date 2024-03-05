import json
import os
import pytest

from pykechain.enums import StoredFileCategory, StoredFileClassification, StoredFileSize
from pykechain.exceptions import NotFoundError
from pykechain.models.stored_file import StoredFile
from pykechain.utils import temp_chdir
from tests.classes import TestBetamax
from PIL import Image


class TestStoredFiles(TestBetamax):
    def setUp(self):
        super().setUp()
        self.test_files_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
        )
        self.upload_path = os.path.join(
            self.test_files_dir,
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


class TestStoredFilesBaseTestCase(TestBetamax):
    def setUp(self):
        super().setUp()
        self.test_files_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
        )
        self.pdf_file_name = "test_upload_pdf.pdf"
        self.upload_pdf_path = os.path.join(
            self.test_files_dir,
            "tests",
            "files",
            "test_upload_image_to_attachment_property",
            self.pdf_file_name,
        )
        self.image_file_name = "test_upload_image.png"
        self.upload_image_path = os.path.join(
            self.test_files_dir,
            "tests",
            "files",
            "test_upload_image_to_attachment_property",
            self.image_file_name,
        )
        self.pdf_stored_file_name = "__TEST_TEMPORARY_STORED_PDF_FILE"
        self.image_stored_file_name = "__TEST_TEMPORARY_STORED_IMAGE_FILE"

        self.stored_pdf_file = self.client.create_stored_file(
            name=self.pdf_stored_file_name,
            scope=self.project,
            classification=StoredFileClassification.SCOPED,
            filepath=self.upload_pdf_path,
            description="__TEST_STORED_FILE_DESCRIPTION",
        )
        self.stored_image_file = self.client.create_stored_file(
            name=self.image_stored_file_name,
            scope=self.project,
            classification=StoredFileClassification.SCOPED,
            filepath=self.upload_image_path,
            description="__TEST_STORED_FILE_DESCRIPTION",
        )
        self.added_stored_file = None

    def tearDown(self):
        if self.stored_pdf_file:
            self.stored_pdf_file.delete()
        if self.stored_image_file:
            self.stored_image_file.delete()
        if self.added_stored_file:
            self.added_stored_file.delete()
        super().tearDown()


@pytest.mark.skipif(
    "os.getenv('TRAVIS', False) or os.getenv('GITHUB_ACTIONS', False)",
    reason="Skipping tests when using Travis or Github Actions, as stored_files "
    "download links have time limited access keys in the uri",
)
class TestStoredFilesDownload(TestStoredFilesBaseTestCase):
    def test_download_pdf_from_stored_file(self):
        with temp_chdir() as target_dir:
            filepath = os.path.join(target_dir, "test_upload_pdf.pdf")
            self.stored_pdf_file.save_as(filename=filepath)

    def test_download_image_from_stored_file(self):
        with temp_chdir() as target_dir:
            filepath = os.path.join(target_dir, "test_upload_image.png")
            self.stored_image_file.save_as(filename=filepath, size=StoredFileSize.M)
            image = Image.open(filepath)
            self.assertEqual(image.width, 200)
            self.assertEqual(image.height, 105)
            self.assertEqual(image.format, "JPEG")


class TestStoredFilesUpload(TestStoredFilesBaseTestCase):
    def setUp(self):
        super().setUp()
        self.test_json_file_name = "test_upload_json.json"
        self.test_figure_file_name = "test_upload_plot.png"

    def tearDown(self):
        super().tearDown()

    def test_upload_file_on_top_of_an_already_existing_one(self):
        self.stored_pdf_file.upload(data=self.upload_image_path)
        self.assertEqual(self.stored_pdf_file.filename, self.image_file_name)
        self.assertEqual(self.stored_pdf_file.content_type, "image/jpeg")

    def test_upload_json_data_to_stored_file(self):
        test_dict = {"a": 1, "b": 3}
        json_data = (
            self.test_json_file_name,
            json.dumps(test_dict),
            "application/json",
        )

        self.stored_pdf_file.upload(data=json_data, name=self.test_json_file_name)

        self.assertEqual(self.stored_pdf_file.filename, self.test_json_file_name)
        self.assertEqual(self.stored_pdf_file.content_type, "application/octet-stream")

    @pytest.mark.skipif(
        "os.getenv('TRAVIS', False) or os.getenv('GITHUB_ACTIONS', False)",
        reason="Skipping tests when using Travis or Github Actions, as not Auth can be provided",
    )
    def test_upload_plot_to_stored_file(self):
        import matplotlib.pyplot as plt
        from matplotlib import lines

        fig = plt.figure()
        fig.add_artist(lines.Line2D([0, 1, 0.5], [0, 1, 0.3]))
        fig.add_artist(lines.Line2D([0, 1, 0.5], [1, 0, 0.2]))

        self.stored_pdf_file.upload(data=fig, name=self.test_figure_file_name)

        self.assertEqual(self.stored_pdf_file.filename, self.test_figure_file_name)
        self.assertEqual(self.stored_pdf_file.content_type, "image/png")
