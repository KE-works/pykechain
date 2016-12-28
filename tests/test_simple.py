from unittest import skip

import betamax
import pykechain

TEST_URL = 'https://kec2api.ke-chain.com'
TEST_USER = 'pykechain' # LVL1
TEST_TOKEN = '***REMOVED***'
TEST_SCOPE_ID = 'b9e3f77b-281b-4e17-8d7c-a457b4d92005'

with betamax.Betamax.configure() as config:
    config.cassette_library_dir = 'tests/cassettes'


class TestApi(object):
    def test_parts(self):
        from pykechain.api import client

        with betamax.Betamax(client.session) as vcr:
            vcr.use_cassette('parts')

            client.login(token="***REMOVED***")

            part_set = client.parts()

            assert len(part_set) == 29

    def test_part(self):
        from pykechain.api import client

        with betamax.Betamax(client.session) as vcr:
            vcr.use_cassette('part')

            client.login(token="***REMOVED***")

            gears = client.part('Bike').property('Gears')

            assert gears.value == 6

# class TestCreatePart(object):
#     def test_update_property_value(self):
#         client = pykechain.Client()