#!/bin/env python
"""
Commandline script to upload any file to KE-chain
"""

import sys

import logging
from envparse import Env

import click

from pykechain import Client

env = Env()
env.read_envfile()

__version__ = '0.1-170119'
URL = env('TEST_URL', default='https://kec2api.ke-chain.com')
USERNAME = env('TEST_USERNAME', default='pykechain')
TOKEN = env('TEST_TOKEN', default='')
SCOPE_ID = env('TEST_SCOPE_ID', default='99d8cf99-41a5-490a-85e6-9dc8301c6cf9')


def parse_arguments():
    from argparse import ArgumentParser
    parser = ArgumentParser('file_uploader',
                            description='Will upload a file to a attachment property in a KE-chain server',
                            version=__version__)
    parser.add_argument('--host-url', '--host_url', '-u', type=str,
                        default=URL,
                        help='Full url of the KE-chain server [Default: "%(default)s"]')
    parser.add_argument('--user', '-U', default=USERNAME,
                        help='Username to access the KE-chain server[Default: "%(default)s"]')
    parser.add_argument('--password', '-p',
                        help='password of the user')
    parser.add_argument('--token', '-t',
                        help='token for the user (optional token API token authentication)')
    parser.add_argument('--scope', '-S', default=SCOPE_ID,
                        help='Scope in the product model [Default: "%(default)s"]')
    parser.add_argument('--property', '-P', type=str,
                        help='property name to attach file to (quotes if the partname has spaces) [Default: "%(default)s"]')
    parser.add_argument('--file', '-f', required=True,
                        help='Filename to upload to the node in the model in the repo')
    parser.add_argument('--logging', '-l', action='store_true',
                        help='Increase Verbosity logginglevel to Debug (Default INFO)')
    return parser.parse_args()


def upload_the_file_to_an_attachment_property(client, property_name, filename):
    # find the property
    # check if attachment property
    # check if file exist
    # uploade the file
    # check result
    target = client.property(name=property)


    pass


def main():
    args = parse_arguments()
    sys.stdout.writelines(['%s : %s\n' % (k, v) for k, v in vars(args).iteritems()])

    if args.logging:
        logging.basicConfig(level=logging.INFO)
        logging.getLogger('suds.client').setLevel(logging.DEBUG)
        logging.getLogger('suds.transport').setLevel(logging.DEBUG)

    client = Client(url=args.url, check_certificates=True)
    if args.token:
        client.login(token=args.token)
    elif args.username and args.password:
        client.login(username=args.username, password=args.password)

    result = upload_the_file_to_an_attachment_property(client, args.property, args.file)

    if result:
        msg = 'File "{}" is successfully uploaded to KE-chain'.format(args.file)
        return 0
    else:
        msg = 'Could not upload'
        return 1


if __name__ == "__main__":
    sys.exit(main())
