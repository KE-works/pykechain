from io import BytesIO

from PIL import Image
from envparse import Env

# reads a local .env file with the TEST_TOKEN=<user token>
# ensure that this file is not commited to github (never ever)
env = Env()
env.read_envfile()

TEST_URL = env("TEST_URL", default="https://pim3-test.ke-chain.com")
TEST_USERNAME = env("TEST_USERNAME", default="pykechain")  # LVL1
TEST_TOKEN = env("TEST_TOKEN", default="")
TEST_SCOPE_ID = env("TEST_SCOPE_ID", default="bd5dceaa-a35e-47b0-9fc5-875410f4a56f")
TEST_SCOPE_NAME = env("TEST_SCOPE_NAME", default="Bike Project")
TEST_RECORD_CASSETTES = env.bool("TEST_RECORD_CASSETTES", default=True)


def create_test_image_file() -> BytesIO:
    """Create an Image file in memory for testing handling upload of Images."""
    image_io = BytesIO()
    Image.new("RGB", (50, 50), color="red").save(image_io, format="jpeg")
    image_io.seek(0)
    return image_io
