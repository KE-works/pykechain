import datetime
import os

import pytest

from pykechain.utils import temp_chdir

from pykechain.models.expiring_download import ExpiringDownload
from tests.classes import TestBetamax


class TestExpiringDownloads(TestBetamax):
    def setUp(self):
        super().setUp()
        self.test_assets_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
        )
        self.test_content_path = os.path.join(
            self.test_assets_dir,
            "tests",
            "files",
            "test_upload_content_to_expiring_download",
            "test_upload_content.pdf",
        )
        self.now = datetime.datetime.now()

        self.test_expiring_download = self.client.create_expiring_download(
            expires_in=56000,
            expires_at=datetime.datetime.now(),
        )

    def tearDown(self):
        self.test_expiring_download.delete()
        super().tearDown()

    def test_create_expiring_download_with_content(self):
        content_path = os.path.join(
            self.test_assets_dir,
            "tests",
            "files",
            "test_upload_content_to_expiring_download",
            "test_upload_content.pdf",
        )
        new_expiring_download = self.client.create_expiring_download(
            expires_at=datetime.datetime.now(),
            expires_in=42000,
            content_path=content_path,
        )
        self.assertTrue(isinstance(new_expiring_download, ExpiringDownload))
        new_expiring_download.delete()

    def test_retrieve_expiring_downloads(self):
        expiring_downloads = self.client.expiring_downloads()
        self.assertTrue(expiring_downloads)

    def test_update_expiring_download(self):
        self.test_expiring_download.edit(expires_in=42000)
        self.assertEqual(self.test_expiring_download.expires_in, 42000)

    def test_upload_expiring_download(self):
        upload_path = os.path.join(
            self.test_assets_dir,
            "tests",
            "files",
            "test_upload_content_to_expiring_download",
            "test_upload_content.pdf",
        )
        self.test_expiring_download.upload(content_path=upload_path)
        self.assertIsNotNone(self.test_expiring_download.filename)
        self.assertEqual(
            self.test_expiring_download.filename, "test_upload_content.pdf"
        )

    def test_upload_wrong_content_path(self):
        upload_path = os.path.join(
            self.test_assets_dir,
            "tests",
            "files",
            "test_upload_content_to_expiring_download",
            "test_upload_content.py",
        )
        with self.assertRaises(OSError):
            self.test_expiring_download.upload(content_path=upload_path)

    @pytest.mark.skipif(
        "os.getenv('TRAVIS', False) or os.getenv('GITHUB_ACTIONS', False)",
        reason="Skipping tests when using Travis or Github Actions, Downloads cannot be provided",
    )
    def test_save_expiring_download_content(self):
        upload_path = os.path.join(
            self.test_assets_dir,
            "tests",
            "files",
            "test_upload_content_to_expiring_download",
            "test_upload_content.pdf",
        )
        self.test_expiring_download.upload(content_path=upload_path)
        with temp_chdir() as target_dir:
            self.test_expiring_download.save_as(target_dir=target_dir)
            self.assertEqual(len(os.listdir(target_dir)), 1)
