from envparse import Env

# reads a local .env file with the TEST_TOKEN=<user token>
# ensure that this file is not commited to github (never ever)

env = Env()
env.read_envfile()

TEST_URL = env('TEST_URL', default='https://kec2api.ke-chain.com')
TEST_USERNAME = env('TEST_USERNAME', default='pykechain')  # LVL1
TEST_TOKEN = env('TEST_TOKEN', default='')
TEST_SCOPE_ID = env('TEST_SCOPE_ID', default='b9e3f77b-281b-4e17-8d7c-a457b4d92005')
