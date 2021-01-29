import datetime
import os

from pykechain.models.expiring_download import ExpiringDownload
from tests.classes import TestBetamax


class TestExpiringDownloads(TestBetamax):
    def setUp(self):
        super(TestExpiringDownloads, self).setUp()
        self.test_expiring_download = self.client.create_expiring_download(
            expires_in=56000
        )

    def tearDown(self):
        self.test_expiring_download.delete()

    def test_create_expiring_download(self):
        # setUp
        new_expiring_download = self.client.create_expiring_download(
            expires_at=datetime.datetime.now(),
        )

        self.assertTrue(isinstance(new_expiring_download, ExpiringDownload))
        return new_expiring_download

    def test_retrieve_expiring_downloads(self):
        expiring_downloads = self.client.expiring_downloads()
        self.assertTrue(expiring_downloads)

    def test_update_expiring_download(self):
        self.test_expiring_download.edit(expires_in=42000)
        self.assertEqual(self.test_expiring_download.expires_in, 42000)
