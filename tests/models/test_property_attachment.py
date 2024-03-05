import json
import os
import unittest

from pykechain.enums import ImageSize, Multiplicity, PropertyType
from pykechain.models import AttachmentProperty
from pykechain.utils import temp_chdir
from tests.classes import TestBetamax
from PIL import Image


class TestAttachment(TestBetamax):
    test_dict = {"a": 1, "b": 3}
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)).replace("\\", "/"))
    )

    def setUp(self):
        super().setUp()
        self.test_assets_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
        )
        self.property_name = "Plot Attachment"

        self.root_model = self.project.model(name="Product")
        self.part_model = self.root_model.add_model(
            name="__Testing attachments", multiplicity=Multiplicity.ONE_MANY
        )
        self.property_model = self.part_model.add_property(
            name=self.property_name, property_type=PropertyType.ATTACHMENT_VALUE
        )  # type: AttachmentProperty

        self.property = self.part_model.instance().property(
            name=self.property_name
        )  # type: AttachmentProperty

    def tearDown(self):
        self.part_model.delete()
        super().tearDown()

    def test_retrieve_attachment(self):
        data = ("data.json", json.dumps(self.test_dict), "application/json")

        self.property._upload(data)

        r = self.property.json_load()

        self.assertDictEqual(r, self.test_dict)

    def test_retrieve_value(self):
        self.assertIsNone(self.property.value)

        self.property.upload(self.project_root + "/requirements.txt")

        self.assertIsNotNone(self.property.value)

    def test_set_value_none(self):
        self.property.value = None
        self.assertFalse(self.property.has_value())

    def test_set_value_not_a_path(self):
        with self.assertRaises(FileNotFoundError):
            self.property.value = "String must be a filepath"

    def test_upload(self):
        self.property.upload(self.project_root + "/requirements.txt")

        requirements = self.project_root + "/requirements.txt"
        self.property.upload(requirements)

    # 1.11.1
    def test_clear_an_attachment_property(self):
        # setUp
        self.property.upload(self.project_root + "/requirements.txt")

        # testing
        self.assertTrue(self.property.has_value())

        self.property.clear()
        self.assertIsNone(self.property.value)
        self.assertIsNone(self.property._value)

    def test_retrieve_filename_from_value(self):
        # setUp
        self.property.upload(self.project_root + "/requirements.txt")

        # testing
        self.assertEqual(self.property.filename, "requirements.txt")

    def test_has_value_true(self):
        # setUp
        self.property.upload(self.project_root + "/requirements.txt")

        # testing
        self.assertTrue(self.property.has_value())

    def test_has_value_false(self):
        self.assertFalse(self.property.has_value())

    def test_add_with_properties(self):
        # setUp
        self.new_wheel = self.root_model.instance().add_with_properties(
            self.part_model,
            "new part",
            update_dict={self.property_name: self.project_root + "/requirements.txt"},
        )

    @unittest.skip("Saving the image cannot be executed when recording cassettes")
    def test_save_as_attachment(self):
        upload_path = os.path.join(
            self.test_assets_dir,
            "files",
            "test_upload_image_to_attachment_property",
            "test_upload_image.png",
        )
        self.property.upload(upload_path)

        with temp_chdir() as target_dir:
            filepath = os.path.join(target_dir, "image_sqxs.png")
            self.property.save_as(filename=filepath, size=ImageSize.SQXS)
            path = os.path.join(target_dir, filepath)
            image_sqxs = Image.open(path)
            self.assertEqual(image_sqxs.width, 100)
            self.assertEqual(image_sqxs.height, 100)
