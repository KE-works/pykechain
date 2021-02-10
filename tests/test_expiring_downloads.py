import datetime
import os

from pykechain.models.expiring_download import ExpiringDownload
from tests.classes import TestBetamax


class TestExpiringDownloads(TestBetamax):
    def setUp(self):
        super(TestExpiringDownloads, self).setUp()
        self.test_assets_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)).replace('\\', '/'))
        self.test_content_path = os.path.join(self.test_assets_dir, 'tests', 'files',
                                              'test_upload_content_to_expiring_download',
                                              'test_upload_content.pdf')
        self.test_expiring_download = self.client.create_expiring_download(
            expires_in=56000,
            expires_at=datetime.datetime.now(),
        )

    def tearDown(self):
        self.test_expiring_download.delete()

    def test_create_expiring_download(self):
        content_path = os.path.join(self.test_assets_dir, 'tests', 'files', 'test_upload_content_to_expiring_download',
                                    'test_upload_content.pdf')
        new_expiring_download = self.client.create_expiring_download(
            expires_at=datetime.datetime.now(),
            expires_in=42000,
            content_path=content_path
        )
        self.assertTrue(isinstance(new_expiring_download, ExpiringDownload))

    def test_retrieve_expiring_downloads(self):
        expiring_downloads = self.client.expiring_downloads()
        self.assertTrue(expiring_downloads)

    def test_update_expiring_download(self):
        self.test_expiring_download.edit(expires_in=42000)
        self.assertEqual(self.test_expiring_download.expires_in, 42000)

    def test_upload_expiring_download(self):
        pass
