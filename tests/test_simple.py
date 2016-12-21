from unittest import skip

import betamax
import pykechain


with betamax.Betamax.configure() as config:
    config.cassette_library_dir = 'tests/cassettes'

@skip
class TestApi(object):
    def test_parts(self):
        from pykechain.api import client

        with betamax.Betamax(client.session) as vcr:
            vcr.use_cassette('parts')

            client.login(token="e920094902818b26feb4fac3dfa2904fff88649c")

            part_set = client.parts()

            assert len(part_set) == 29

    def test_part(self):
        from pykechain.api import client

        with betamax.Betamax(client.session) as vcr:
            vcr.use_cassette('part')

            client.login(token="e920094902818b26feb4fac3dfa2904fff88649c")

            gears = client.part('Bike').property('Gears')

            assert gears.value == 6
