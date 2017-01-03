from pykechain.exceptions import NotFoundError
from tests.classes import TestBetamax


class TestAttachment(TestBetamax):

    test_dict = {'a': 1, 'b': 2}

    def test_retrieve_attachment(self):
        project = self.client.scope('Bike Project')
        picture = project.part('Bike').property('Picture')

        r = picture._download().json()

        self.assertDictEqual(r, self.test_dict)
