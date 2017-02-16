import json

from tests.classes import TestBetamax


class TestAttachment(TestBetamax):

    test_dict = {'a': 1, 'b': 3}

    def test_retrieve_attachment(self):
        project = self.client.scope('Bike Project (pykechain testing)')
        picture = project.part('Bike').property('Picture')

        data = ('data.json', json.dumps(self.test_dict), 'application/json')

        picture._upload(data)

        r = picture._download().json()

        self.assertDictEqual(r, self.test_dict)
