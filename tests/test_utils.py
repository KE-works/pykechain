from unittest import TestCase

from pykechain.utils import is_url, is_valid_email, Empty, get_in_chunks
from tests.classes import SixTestCase


class TestIsURL(SixTestCase):
    def test_is_url_returns_true_on_valid_url(self):
        addresses = [
            u"http://foobar.dk",
            u"http://foobar.museum/foobar",
            u"http://fo.com",
            u"http://FOO.com",
            u"http://foo.com/blah_blah",
            u"http://foo.com/blah_blah/",
            u"http://foo.com/blah_blah_(wikipedia)",
            u"http://foo.com/blah_blah_(wikipedia)_(again)",
            u"http://www.example.com/wpstyle/?p=364",
            u"https://www.example.com/foo/?bar=baz&inga=42&quux",
            u"https://www.example.com?bar=baz",
            u"http://✪df.ws/123",
            u"http://userid:password@example.com:8080",
            u"http://userid@example.com",
            u"http://userid@example.com:8080/",
            u"http://userid:password@example.com",
            u"http://142.42.1.1/",
            u"http://142.42.1.1:8080/",
            u"http://⌘.ws/",
            u"http://foo.com/blah_(wikipedia)#cite-1",
            u"http://foo.com/unicode_(✪)_in_parens",
            u"http://foo.com/(something)?after=parens",
            u"http://☺.damowmow.com/",
            u"http://code.google.com/events/#&product=browser",
            u"http://j.mp",
            u"ftp://foo.bar/baz",
            u"http://foo.bar/?q=Test%20URL-encoded%20stuff",
            u"http://-.~_!$&'()*+,;=:%40:80%2f::::::@example.com",
            u"http://1337.net",
            u"http://a.b-c.de",
            u"http://223.255.255.254",
            u"http://127.0.10.150",
            u"http://localhost",
            u"http://localhost:8000",
            u"http://[FEDC:BA98:7654:3210:FEDC:BA98:7654:3210]:80/index.html",
            u"http://[1080:0:0:0:8:800:200C:417A]/index.html",
            u"http://[3ffe:2a00:100:7031::1]",
            u"http://[1080::8:800:200C:417A]/foo",
            u"http://[::192.9.5.5]/ipng",
            u"http://[::FFFF:129.144.52.38]:80/index.html",
            u"http://[2010:836B:4179::836B:4179]",
        ]
        for address in addresses:
            with self.subTest(address):
                self.assertTrue(is_url(address),  "should be a valid address: '{}'".format(address))

    def test_is_url_returns_False_on_failed_url(self):
        failed_addresses = [
            "http://foobar",
            "foobar.dk",
            "http://127.0.0/asdf",
            "http://foobar.d",
            "http://foobar.12",
            "http://foobar",
            "htp://foobar.com",
            "http://foobar..com",
            "http://fo..com",
            "http://",
            "http://.",
            "http://..",
            "http://../",
            "http://?",
            "http://??",
            "http://??/",
            "http://#",
            "http://##",
            "http://##/",
            "http://foo.bar?q=Spaces should be encoded",
            "//",
            "//a",
            "///a",
            "///",
            "http:///a",
            "foo.com",
            "rdar://1234",
            "h://test",
            "http:// shouldfail.com",
            ":// should fail",
            "http://foo.bar/foo(bar)baz quux",
            "ftps://foo.bar/",
            "http://-error-.invalid/",
            "http://a.b--c.de/",
            "http://-a.b.co",
            "http://a.b-.co",
            "http://0.0.0.0",
            "http://10.1.1.0",
            "http://10.1.1.255",
            "http://224.1.1.1",
            "http://1.1.1.1.1",
            "http://123.123.123",
            "http://3628126748",
            "http://.www.foo.bar/",
            "http://www.foo.bar./",
            "http://.www.foo.bar./",
            "http://127.12.0.260",
            'http://example.com/">user@example.com',
            "http://[2010:836B:4179::836B:4179",
            "http://2010:836B:4179::836B:4179",
            "http://2010:836B:4179::836B:4179:80/index.html",
        ]
        for address in failed_addresses:
            with self.subTest(address):
                self.assertFalse(is_url(address), "should be a invalid address: '{}'".format(address))


class TestIsEmail(SixTestCase):
    def test_is_email_returns_true_on_valid_url(self):
        valid_addresses = [
            "some@domain.org",
            "email@example.com",
            "firstname.lastname@example.com",
            "email@subdomain.example.com",
            "firstname+lastname@example.com",
            "email@123.123.123.123",
            "email@[123.123.123.123]",
            '"email"@example.com',
            "1234567890@example.com",
            "email@example-one.com",
            "_______@example.com",
            "email@example.name",
            "email@example.museum",
            "email@example.co.jp",
            "firstname-lastname@example.com",
        ]
        for email in valid_addresses:
            with self.subTest(email):
                self.assertTrue(is_valid_email(email),  "should be a valid address: '{}'".format(email))

    def test_is_email_returns_false_on_invalid_url(self):
        invalid_addresses = [
            "plainaddress",
            "#@%^%#$@#$@#.com",
            "@example.com",
            "Joe Smith <email@example.com>",
            "email.example.com",
            "email@example@example.com",
            ".email@example.com",
            "email.@example.com",
            "email..email@example.com",
            "あいうえお@example.com",
            "email@example.com (Joe Smith)",
            "email@example",
            "email@-example.com",
            "email@example..com",
            "Abc..123@example.com",
            "”(),:;<>[\]@example.com",
            "just”not”right@example.com",
            'this\ is"really"not\allowed@example.com',
        ]
        for email in invalid_addresses:
            with self.subTest(email):
                self.assertFalse(is_valid_email(email), "should be an invalid address: '{}'".format(email))


class TestEmpty(TestCase):

    def test_singleton(self):
        empty_1 = Empty()
        empty_2 = Empty()

        self.assertEqual(empty_1, empty_2)
        self.assertIs(empty_1, empty_2)
        self.assertIsNot(empty_1, Empty)


class TestChunks(TestCase):

    def test_get_in_chunks(self):
        chunks = get_in_chunks(
            lst=list(range(77)),
            chunk_size=9,
        )

        import types
        self.assertIsInstance(chunks, types.GeneratorType)

        chunks_list = list(chunks)
        self.assertEqual(9, len(chunks_list))
