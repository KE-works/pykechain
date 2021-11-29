from unittest import TestCase

from pykechain.utils import Empty, get_in_chunks, is_url, is_valid_email


class TestIsURL(TestCase):
    def test_is_url_returns_true_on_valid_url(self):
        addresses = [
            "http://foobar.dk",
            "http://foobar.museum/foobar",
            "http://fo.com",
            "http://FOO.com",
            "http://foo.com/blah_blah",
            "http://foo.com/blah_blah/",
            "http://foo.com/blah_blah_(wikipedia)",
            "http://foo.com/blah_blah_(wikipedia)_(again)",
            "http://www.example.com/wpstyle/?p=364",
            "https://www.example.com/foo/?bar=baz&inga=42&quux",
            "https://www.example.com?bar=baz",
            "http://✪df.ws/123",
            "http://userid:password@example.com:8080",
            "http://userid@example.com",
            "http://userid@example.com:8080/",
            "http://userid:password@example.com",
            "http://142.42.1.1/",
            "http://142.42.1.1:8080/",
            "http://⌘.ws/",
            "http://foo.com/blah_(wikipedia)#cite-1",
            "http://foo.com/unicode_(✪)_in_parens",
            "http://foo.com/(something)?after=parens",
            "http://☺.damowmow.com/",
            "http://code.google.com/events/#&product=browser",
            "http://j.mp",
            "ftp://foo.bar/baz",
            "http://foo.bar/?q=Test%20URL-encoded%20stuff",
            "http://-.~_!$&'()*+,;=:%40:80%2f::::::@example.com",
            "http://1337.net",
            "http://a.b-c.de",
            "http://223.255.255.254",
            "http://127.0.10.150",
            "http://localhost",
            "http://localhost:8000",
            "http://[FEDC:BA98:7654:3210:FEDC:BA98:7654:3210]:80/index.html",
            "http://[1080:0:0:0:8:800:200C:417A]/index.html",
            "http://[3ffe:2a00:100:7031::1]",
            "http://[1080::8:800:200C:417A]/foo",
            "http://[::192.9.5.5]/ipng",
            "http://[::FFFF:129.144.52.38]:80/index.html",
            "http://[2010:836B:4179::836B:4179]",
        ]
        for address in addresses:
            with self.subTest(address):
                self.assertTrue(is_url(address), f"should be a valid address: '{address}'")

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
                self.assertFalse(is_url(address), f"should be a invalid address: '{address}'")


class TestIsEmail(TestCase):
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
                self.assertTrue(is_valid_email(email), f"should be a valid address: '{email}'")

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
            r"”(),:;<>[\]@example.com",
            "just”not”right@example.com",
            'this\\ is"really"not\allowed@example.com',
        ]
        for email in invalid_addresses:
            with self.subTest(email):
                self.assertFalse(is_valid_email(email), f"should be an invalid address: '{email}'")


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
