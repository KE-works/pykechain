"""All pykechain configuration constants will be listed here."""

# Configuration of async download of activity pdf exports
import pytz

ASYNC_REFRESH_INTERVAL = 2  # seconds
ASYNC_TIMEOUT_LIMIT = 100  # seconds

# timezone of the server, normally always in UTC
SERVER_TIMEZONE = pytz.UTC
