import json

from tests.classes import TestBetamax


class TestAttachment(TestBetamax):

    test_dict = {'a': 1, 'b': 3}

    def test_retrieve_attachment(self):
        attach = self.project.part('One').property('Attachment')

        data = ('data.json', json.dumps(self.test_dict), 'application/json')

        attach._upload(data)

        r = attach._download().json()

        self.assertDictEqual(r, self.test_dict)

        # TODO: attach._upload(None) or attach.clear() for fixture consistency
