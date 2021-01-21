import datetime
import os

from tests.classes import TestBetamax


class TestExpiringDownloads(TestBetamax):
    def test_create_expiring_download(self):
        # setUp
        new_expiring_download = self.client.create_expiring_download(
            expires_at=datetime.datetime.now()
        )

        self.assertEqual(new_expiring_download._json_data['content'], 'test_upload_script.py')
        return new_expiring_download

    # def setUp(self):
    #     super(TestExpiringDownloads, self).setUp()
    #     self.test_assets_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)).replace('\\', '/'))
    #
    # def test_retrieve_expiring_downloads(self):
    #     self.assertTrue(self.project.expiring_downloads())
