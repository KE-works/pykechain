import os

import pytest
from betamax import Betamax

from pykechain import Client

TEST_URL = 'https://kec2api.ke-chain.com'
TEST_USER = 'pykechain'  # LVL1
TEST_TOKEN = 'e1a927342b47288fe9ee3e52ebf7e08c149dd005'
TEST_SCOPE_ID = 'b9e3f77b-281b-4e17-8d7c-a457b4d92005'


# class BaseAPITest(object):
#     """
#     Base API test class for Betamax enabled KEC API tests
#     """
#
#     def __init__(self):
#         """
#         Initialises and exposes the client (pykechain.Client) connected to TEST_URL
#         Initialises and exposes betamax vcr on the client.
#
#         Example
#         -------
#
#         def test_foo_bar(self):
#             with self.betamax as vcr:
#                 vcr.use_cassette(__name__)
#                 self.client.login(token=TEST_TOKEN)
#                 # do testing here
#
#         """
#         self.client = Client(url=TEST_URL)
#         self.betamax = Betamax(self.client)
#         self.betamax.configure().cassette_library_dir = BETAMAX_CASSETTES_DIR


def get_method_name():
    """
    returns the function name
    :return: name of the function
    """
    import inspect
    return inspect.stack()[1][3]
