import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import json
import os
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
        photo_attach = self.project.part('Bike').property('Photo Attachment')
        photo_attach_expected_value = '[Attachment: Awesome.jpg]'
        photo_attach_actual_value = photo_attach.value

        self.assertEqual(photo_attach_expected_value, photo_attach_actual_value)

        picture = self.project.part('Bike').property('Picture')

        self.assertEqual(picture.value, None)

    def test_set_value(self):
        picture = self.project.part('Bike').property('Picture')

        with self.assertRaises(RuntimeError):
            picture.value = 'Should never work'

    def test_upload(self):
        plot_attach = self.project.part('Bike').property('Plot Attachment')

        # Test the upload of matplotlib figures
        fig = plt.figure(1)
        plt.plot([1, 2, 3, 4], [1, 4, 9, 16], 'ro')
        plt.axis([0, 6, 0, 20])
        plt.close(fig)
        plot_attach.upload(fig)

        # Test the upload of regular data (such a .txt file)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)).replace('\\', '/')))
        requirements = project_root + '/requirements.txt'
        plot_attach.upload(requirements)

