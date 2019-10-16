import json
import os

from pykechain.enums import PropertyType
from pykechain.models import AttachmentProperty2
from tests.classes import TestBetamax


class TestAttachment(TestBetamax):
    test_dict = {'a': 1, 'b': 3}

    def test_retrieve_attachment(self):
        picture = self.project.part('Bike').property('Picture')

        data = ('data.json', json.dumps(self.test_dict), 'application/json')

        picture._upload(data)

        r = picture.json_load()

        self.assertDictEqual(r, self.test_dict)

    def test_retrieve_value(self):
        photo_attach = self.project.part('Bike').property('Picture')
        photo_attach_expected_value = '[Attachment: Awesome.jpg]'
        photo_attach_actual_value = photo_attach.value

        self.assertIsNotNone(photo_attach_actual_value)

        empty_attach = self.project.model('Bike').property('Picture')

        self.assertIsNone(empty_attach.value)

    def test_set_value_none(self):
        picture = self.project.part('Bike').property('Picture')
        picture.value = None

    def test_set_value(self):
        picture = self.project.part('Bike').property('Picture')

        with self.assertRaises(FileNotFoundError):
            picture.value = 'String must be a filepath'

    def test_upload(self):
        # setup
        plot_attach_model = self.project.model('Bike').add_property(
            name='Plot Attachment',
            property_type=PropertyType.ATTACHMENT_VALUE
        )
        plot_attach = self.project.part('Bike').property('Plot Attachment')

        # Test the upload of regular data (such a .txt file)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)).replace('\\', '/')))
        requirements = project_root + '/requirements.txt'
        plot_attach.upload(requirements)

        # teardown
        plot_attach_model.delete()

    # 1.11.1
    def test_clear_an_attachment_property(self):
        # setUp
        plot_attach_model = self.project.model('Bike').add_property(
            name='Plot Attachment',
            property_type=PropertyType.ATTACHMENT_VALUE
        )
        plot_attach = self.project.part('Bike').property('Plot Attachment')

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)).replace('\\', '/')))
        requirements = project_root + '/requirements.txt'
        plot_attach.upload(requirements)
        plot_attach_u = self.project.part('Bike').property('Plot Attachment')

        # testing
        self.assertTrue(plot_attach_u.value.find('requirements.txt'))

        plot_attach.clear()
        self.assertEqual(plot_attach.value, None)
        self.assertEqual(plot_attach._value, None)

        # teardown
        plot_attach_model.delete()

    def test_retrieve_filename_from_value(self):
        photo_attach = self.project.part('Bike').property('Picture')  # type: AttachmentProperty2
        photo_attach_actual_filename = photo_attach.filename

        self.assertEqual(photo_attach.filename, photo_attach.filename)
