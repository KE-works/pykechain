import betamax
import kechain2

with betamax.Betamax.configure() as config:
    config.cassette_library_dir = 'cassettes'


class TestApi(object):
    def test_parts(self):
        from kechain2.api import session

        kechain2.login("***REMOVED***")

        with betamax.Betamax(session) as vcr:
            vcr.use_cassette('parts')

            part_set = kechain2.parts()

            assert len(part_set) == 29
