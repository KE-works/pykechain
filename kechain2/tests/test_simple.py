import betamax
import kechain2

with betamax.Betamax.configure() as config:
    config.cassette_library_dir = 'kechain2/tests/cassettes'


class TestApi(object):
    def test_parts(self):
        from kechain2.api import session

        kechain2.login("4fd189d669793373264dc188ce902a2af99d90bc")

        with betamax.Betamax(session) as vcr:
            vcr.use_cassette('parts')

            part_set = kechain2.parts()

            assert len(part_set) == 29
