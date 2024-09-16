import os
from datetime import datetime

from pykechain.enums import PropertyType, StoredFileClassification
from pykechain.models import SignatureProperty
from tests.classes import TestBetamax
from tests.utils import create_test_image_file


class TestPropertySignatureProperty(TestBetamax):
    def setUp(self):
        super().setUp()

        self.wheel_model = self.project.model("Wheel")
        self.bike = self.project.model("Bike")

        self.test_files_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
        )
        self.test_image = create_test_image_file()
        self.file_name = "__TEST_SIGNATURE_STORED_FILE"
        self.signature_stored_file = self.client.create_stored_file(
            name=self.file_name,
            scope=self.project,
            classification=StoredFileClassification.SCOPED,
            filepath=self.test_image,
            description="__TEST_STORED_FILE_DESCRIPTION",
        )

        self.test_signature_property_model: SignatureProperty = self.bike.add_property(
            name=f"__Test signature property @ {datetime.now()}",
            property_type=PropertyType.SIGNATURE_VALUE,
            description="Description of test signature property",
            unit="no unit",
            default_value=None,
        )

    def tearDown(self):
        self.test_signature_property_model.delete()
        self.signature_stored_file.delete()
        super().tearDown()

    def test_create_signature_property(self):
        # implicit inside the setUp
        pass

    def test_upload_new_signature_to_property(self):
        self.test_signature_property_model.value = self.signature_stored_file

        self.test_signature_property_model.refresh()
        self.assertIsNotNone(self.test_signature_property_model.value)
