import betamax
import pykechain


with betamax.Betamax.configure() as config:
    config.cassette_library_dir = 'kechain2/tests/cassettes'


class TestApi(object):
    def test_parts(self):
        from pykechain.api import client

        with betamax.Betamax(client.session) as vcr:
            vcr.use_cassette('parts')

            pykechain.login(token="e920094902818b26feb4fac3dfa2904fff88649c")

            part_set = pykechain.parts()

            assert len(part_set) == 29

    def test_part(self):
        from pykechain.api import client

        with betamax.Betamax(client.session) as vcr:
            vcr.use_cassette('part')

            pykechain.login(token="e920094902818b26feb4fac3dfa2904fff88649c")

            gears = pykechain.part('Bike').property('Gears')

            assert gears.value == 6
