import datetime

import pytz

from pykechain.exceptions import APIError, NotFoundError, MultipleFoundError, IllegalArgumentError
from pykechain.models.banner import Banner
from tests.classes import TestBetamax

NEW_YEAR_2020_naive = datetime.datetime.strptime("2020-01-01T00:01:00", "%Y-%m-%dT%H:%M:%S")
NEW_YEAR_2020 = NEW_YEAR_2020_naive.replace(tzinfo=pytz.UTC)


class TestBanners(TestBetamax):
    TEXT = "__This is a test banner__"
    URL = "https://www.ke-chain.nl/"
    ICON = "poo-storm"

    KWARGS = dict(
        text=TEXT,
        icon=ICON,
        active_from=NEW_YEAR_2020,
    )

    def setUp(self):
        super().setUp()
        self.banner = self.client.create_banner(
            url=self.URL, is_active=True, **self.KWARGS
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
        self.banner.delete()
        self.banner = self.client.create_banner(**self.KWARGS)

    def test_create_invalid_inputs(self):
        self.banner.delete()
        with self.assertRaises(IllegalArgumentError):
            self.banner = self.client.create_banner(
                text=3, icon=self.ICON, active_from=NEW_YEAR_2020
            )
        with self.assertRaises(IllegalArgumentError):
            self.banner = self.client.create_banner(
                text="some text", icon=True, active_from=NEW_YEAR_2020
            )
        with self.assertRaises(IllegalArgumentError):
            self.banner = self.client.create_banner(
                text="some text", icon=self.ICON, active_from=2
            )
        with self.assertRaises(IllegalArgumentError):
            self.banner = self.client.create_banner(active_until="later", **self.KWARGS)
        with self.assertRaises(IllegalArgumentError):
            self.banner = self.client.create_banner(is_active=1, **self.KWARGS)
        with self.assertRaises(IllegalArgumentError):
            self.banner = self.client.create_banner(url="www.ke-chain/scopes/", **self.KWARGS)

    def test_delete(self):
        banner_id = self.banner.id
        self.banner.delete()

        with self.assertRaises(APIError, msg="Cant delete the same banner twice."):
            self.banner.delete()
        with self.assertRaises(NotFoundError, msg="Banner is still found!"):
            self.client.banner(pk=banner_id)

    def test_get_banners(self):
        all_banners = self.client.banners()

        self.assertIsInstance(all_banners, list)
        self.assertTrue(all_banners)

        first_banner = all_banners[0]

        self.assertIsInstance(first_banner, Banner)

    def test_get_banners_invalid_inputs(self):
        with self.assertRaises(IllegalArgumentError):
            self.client.banners(pk=1)
        with self.assertRaises(IllegalArgumentError):
            self.client.banners(text=False)
        with self.assertRaises(IllegalArgumentError):
            self.client.banners(is_active="")

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
        text = "__RENAMED BANNER"
        icon = "site-map"
        url = "https://www.google.com/"
        later = NEW_YEAR_2020 + datetime.timedelta(hours=1)

        self.banner.edit(
            text=text,
            icon=icon,
            active_from=NEW_YEAR_2020,
            active_until=later,
            is_active=False,
            url=url,
        )

        self.assertEqual(text, self.banner.text)
        self.assertEqual(icon, self.banner.icon)
        self.assertEqual(NEW_YEAR_2020, self.banner.active_from)
        self.assertEqual(later, self.banner.active_until)
        self.assertFalse(self.banner.is_active)
        self.assertEqual(url, self.banner.url)

    def test_edit_single_inputs(self):
        for kwarg in [
            dict(text="New text"),
            dict(icon="gifts"),
            dict(active_from=NEW_YEAR_2020 - datetime.timedelta(days=1)),
            dict(active_until=NEW_YEAR_2020 + datetime.timedelta(weeks=1)),
            dict(is_active=False),
            dict(url="https://www.google.com"),
        ]:
            with self.subTest(msg=kwarg):
                self.banner.edit(**kwarg)

    # noinspection PyTypeChecker
    def test_edit_invalid_inputs(self):
        with self.assertRaises(IllegalArgumentError):
            self.banner.edit(text=True)
        with self.assertRaises(IllegalArgumentError):
            self.banner.edit(icon=50)
        with self.assertRaises(IllegalArgumentError):
            self.banner.edit(active_from="now")
        with self.assertRaises(IllegalArgumentError):
            self.banner.edit(active_until="later")
        with self.assertRaises(IllegalArgumentError):
            self.banner.edit(url="ke-chain,com")
        with self.assertRaises(IllegalArgumentError):
            self.banner.edit(is_active="Yes")

    # test added due to #847 - providing no inputs overwrites values
    def test_edit_banner_clear_values(self):
        # setup
        initial_text = "Happy new Year"
        initial_icon = "gifts"
        initial_active_from = NEW_YEAR_2020 - datetime.timedelta(days=1)
        initial_active_until = NEW_YEAR_2020 + datetime.timedelta(days=1)
        initial_is_active = False
        initial_url = "https://www.google.com"

        self.banner.edit(
            text=initial_text,
            icon=initial_icon,
            active_from=NEW_YEAR_2020 - datetime.timedelta(days=1),
            active_until=NEW_YEAR_2020 + datetime.timedelta(days=1),
            is_active=initial_is_active,
            url=initial_url,
        )

        # Edit without mentioning values, everything should stay the same
        new_text = "2021!!!"
        new_is_active = True

        self.banner.edit(text=new_text, is_active=new_is_active)

        # testing
        self.assertEqual(self.banner.text, new_text)
        self.assertEqual(self.banner.icon, initial_icon)
        self.assertEqual(self.banner.active_from, initial_active_from)
        self.assertEqual(self.banner.active_until, initial_active_until)
        self.assertEqual(self.banner.is_active, new_is_active)
        self.assertEqual(self.banner.url, initial_url)

        # Edit with clearing the values, name and status cannot be cleared
        self.banner.edit(
            text=None, icon=None, active_from=None, active_until=None, is_active=None, url=None
        )

        self.assertEqual(self.banner.text, new_text)
        self.assertEqual(self.banner.icon, "")
        self.assertEqual(self.banner.active_from, initial_active_from)
        self.assertEqual(self.banner.active_until, initial_active_until)
        self.assertEqual(self.banner.is_active, new_is_active)
        self.assertEqual(self.banner.url, "")
