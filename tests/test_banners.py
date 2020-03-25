import datetime

from pykechain.exceptions import APIError, NotFoundError, MultipleFoundError
from pykechain.models.banner import Banner
from tests.classes import TestBetamax


class TestBanners(TestBetamax):
    TEXT = '__This is a test banner__'
    URL = 'https://www.ke-chain.nl/'
    ICON = 'poo-storm'
    TZ = datetime.timezone(offset=datetime.timedelta(hours=1))
    NOW = datetime.datetime.now(tz=TZ)

    def setUp(self):
        super().setUp()
        self.banner = self.client.create_banner(
            active_from=self.NOW,
            text=self.TEXT,
            icon=self.ICON,
            url=self.URL,
            is_active=True,
        )  # type: Banner

    def tearDown(self):
        if self.banner:
            try:
                self.banner.delete()
            except APIError:
                pass
        super().tearDown()

    def test_create(self):
        self.assertIsInstance(self.banner, Banner)
        self.assertEqual(self.TEXT, self.banner.text)
        self.assertEqual(self.URL, self.banner.url)
        self.assertEqual(self.ICON, self.banner.icon)
        self.assertTrue(self.banner.is_active)

    def test_create_empty(self):
        banner = self.client.create_banner(
            text=self.TEXT,
            active_from=self.NOW,
            icon=self.ICON,
        )
        banner.delete()

    def test_delete(self):
        banner_id = self.banner.id
        self.banner.delete()

        with self.assertRaises(APIError, msg='Cant delete the same banner twice.'):
            self.banner.delete()
        with self.assertRaises(NotFoundError, msg='Banner is still found!'):
            self.client.banner(pk=banner_id)

    def test_get_banners(self):
        all_banners = self.client.banners()

        self.assertIsInstance(all_banners, list)
        self.assertTrue(all_banners)

        first_banner = all_banners[0]

        self.assertIsInstance(first_banner, Banner)

    def test_get_banner(self):
        banner = self.client.banner(text=self.TEXT)

        self.assertTrue(banner)
        self.assertIsInstance(banner, Banner)

        with self.assertRaises(MultipleFoundError):
            self.client.banner()

    def test_get_active_banner(self):
        active_banner = self.client.active_banner()

        self.assertIsNotNone(active_banner)
        self.assertIsInstance(active_banner, Banner)
        self.assertEqual(self.banner, active_banner)

    def test_edit(self):
        text = '__RENAMED BANNER'
        icon = 'site-map'
        url = 'https://www.google.com/'
        later = datetime.datetime.now(tz=self.TZ)

        self.banner.edit(
            text=text,
            icon=icon,
            active_from=self.NOW,
            active_until=later,
            is_active=False,
            url=url,
        )

        self.assertEqual(text, self.banner.text)
        self.assertEqual(icon, self.banner.icon)
        self.assertEqual(self.NOW, self.banner.active_from)
        self.assertEqual(later, self.banner.active_until)
        self.assertFalse(self.banner.is_active)
        self.assertEqual(url, self.banner.url)
