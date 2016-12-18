import betamax
import kechain2


with betamax.Betamax.configure() as config:
    config.cassette_library_dir = 'kechain2/tests/cassettes'


class TestApi(object):
    def test_parts(self):
        from kechain2.api import client

        with betamax.Betamax(client.session) as vcr:
            vcr.use_cassette('parts')

            kechain2.login(token="e920094902818b26feb4fac3dfa2904fff88649c")

            part_set = kechain2.parts()

            assert len(part_set) == 29

    def test_part(self):
        from kechain2.api import client

        with betamax.Betamax(client.session) as vcr:
            vcr.use_cassette('part')

            kechain2.login(token="e920094902818b26feb4fac3dfa2904fff88649c")

            gears = kechain2.part('Bike').property('Gears')

            assert gears.value == 6
