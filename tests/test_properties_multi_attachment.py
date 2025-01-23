import os
from pathlib import Path

from pykechain.enums import PropertyType
from pykechain.models.stored_file import StoredFile
from pykechain.models.validators import SingleReferenceValidator
from tests.classes import TestBetamax


class TestMultiAttachmentProperties(TestBetamax):
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

        self.wheel_model = self.project.model("Wheel")
        self.bike_model = self.project.model("Bike")
        self.prop_name = "__Test MAP property"
        self.prop_model = self.bike_model.add_property(
            name=self.prop_name,
            property_type=PropertyType.STOREDFILE_REFERENCES_VALUE,
            description="description of the property",
            unit="unit of the property",
            validators=[SingleReferenceValidator],
        )
        self.bike = self.bike_model.instance()
        self.prop = self.bike.property(name=self.prop_name)

    def tearDown(self):
        if self.prop_model:
            self.prop_model.delete()
        super().tearDown()

    def test_get_multi_attachment_property_single_ref_validators(self):
        self.prop_model.validators = (SingleReferenceValidator(),)
        self.prop.refresh()
        self.assertTrue(self.prop.has_validator(SingleReferenceValidator))

    def test_single_stored_file_references_property_value_gets_replaces(self):
        self.prop_model.validators = (SingleReferenceValidator(),)
        self.prop.refresh()
        self.prop.upload(self.upload_path)
        self.prop.refresh()
        self.assertIsInstance(self.prop.value, list)
        self.assertEqual(len(self.prop.value), 1)
        self.assertIsInstance(self.prop.value[0], StoredFile)

        # replace
        self.prop.upload(self.upload_path)
        self.prop.refresh()
        self.assertEqual(len(self.prop.value), 1)
        self.assertIsInstance(self.prop.value[0], StoredFile)
