import json
import os

from pykechain.enums import PropertyType
from pykechain.models import AttachmentProperty2
from tests.classes import TestBetamax


class TestAttachment(TestBetamax):
    test_dict = {'a': 1, 'b': 3}
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)).replace('\\', '/')))

    def setUp(self):
        super(TestAttachment, self).setUp()
        self.property_name = 'Plot Attachment'

        self.bike_model = self.project.model('Bike')
        self.property_model = self.bike_model.add_property(
            name=self.property_name,
            property_type=PropertyType.ATTACHMENT_VALUE
        )  # type: AttachmentProperty2

        self.bike = self.bike_model.instance()
        self.property = self.bike.property(name=self.property_name)

    def tearDown(self):
        self.property_model.delete()
        super(TestAttachment, self).tearDown()

    def test_retrieve_attachment(self):
        data = ('data.json', json.dumps(self.test_dict), 'application/json')

        self.property._upload(data)

        r = self.property.json_load()

        self.assertDictEqual(r, self.test_dict)

    def test_retrieve_value(self):
        self.assertIsNone(self.property.value)

        self.property.upload(self.project_root + '/requirements.txt')
        self.property.refresh()

        self.assertIsNotNone(self.property.value)

    def test_set_value_none(self):
        self.property.value = None
        self.assertFalse(self.property.has_value())

    def test_set_value_not_a_path(self):
        with self.assertRaises(FileNotFoundError):
            self.property.value = 'String must be a filepath'

    def test_upload(self):
        self.property.upload(self.project_root + '/requirements.txt')
        self.property.refresh()

        requirements = self.project_root + '/requirements.txt'
        self.property.upload(requirements)

    # 1.11.1
    def test_clear_an_attachment_property(self):
        # setUp
        self.property.upload(self.project_root + '/requirements.txt')
        self.property.refresh()

        # testing
        self.assertTrue(self.property.has_value())

        self.property.clear()
        self.assertIsNone(self.property.value)
        self.assertIsNone(self.property._value)

    def test_retrieve_filename_from_value(self):
        # setUp
        self.property.upload(self.project_root + '/requirements.txt')
        self.property.refresh()

        # testing
        self.assertEqual(self.property.filename, 'requirements.txt')

    def test_has_value_true(self):
        # setUp
        self.property.upload(self.project_root + '/requirements.txt')
        self.property.refresh()

        # testing
        self.assertTrue(self.property.has_value())

    def test_has_value_false(self):
        self.assertFalse(self.property.has_value())
