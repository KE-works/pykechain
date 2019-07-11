from envparse import Env

# reads a local .env file with the TEST_TOKEN=<user token>
# ensure that this file is not commited to github (never ever)
env = Env()
env.read_envfile()

# TEST_URL = env('TEST_URL', default='https://kec2api.ke-chain.com')
TEST_URL = env('TEST_URL', default='https://pim3-test.ke-chain.com')
TEST_USERNAME = env('TEST_USERNAME', default='pykechain')  # LVL1
TEST_TOKEN = env('TEST_TOKEN', default='')
TEST_SCOPE_ID = env('TEST_SCOPE_ID', default='2c597004-46bd-4027-b650-46504c9d32a6')
# TEST_SCOPE_NAME = env('TEST_SCOPE_NAME', default='Bike Project (pykechain testing)')
TEST_SCOPE_NAME = env('TEST_SCOPE_NAME', default='Bike Project')
TEST_RECORD_CASSETTES = env.bool('TEST_RECORD_CASSETTES', default=True)

# flags for altering testing behaviour (to skip test) for major API changes requiring different tests.
TEST_FLAG_IS_WIM2 = env.bool('TEST_FLAG_IS_WIM2', default=True)
TEST_FLAG_IS_PIM2 = env.bool('TEST_FLAG_IS_PIM2', default=True)
