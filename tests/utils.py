from envparse import Env

# reads a local .env file with the TEST_TOKEN=<user token>
# ensure that this file is not commited to github (never ever)

env = Env()
env.read_envfile()

TEST_URL = env('TEST_URL', default='https://kec2api.ke-chain.com')
TEST_USERNAME = env('TEST_USERNAME', default='pykechain')  # LVL1
TEST_TOKEN = env('TEST_TOKEN', default='9cb723451bc0c736a2ed8b77bebb72528621dad3')
TEST_SCOPE_ID = env('TEST_SCOPE_ID', default='6f7bc9f0-228e-4d3a-9dc0-ec5a75d73e1d')
TEST_SCOPE_NAME = env('TEST_SCOPE_NAME', default='Bike Project (pykechain testing)')
