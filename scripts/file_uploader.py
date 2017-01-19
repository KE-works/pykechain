#!/usr/bin/env python
"""
Commandline script to upload any file to KE-chain
"""
from __future__ import print_function

import logging
import os
import sys

from envparse import Env

try:
    from pykechain import Client
except ImportError:
    sys.path.append('..')
    from pykechain import Client

from pykechain.models import AttachmentProperty
from pykechain.exceptions import NotFoundError, MultipleFoundError, LoginRequiredError

env = Env()
env.read_envfile('../.env')

__version__ = '0.1-170119'
URL = env('TEST_URL', default='https://kec2api.ke-chain.com')
USERNAME = env('TEST_USERNAME', default='pykechain')
TOKEN = env('TEST_TOKEN', default='')
SCOPE_ID = env('TEST_SCOPE_ID', default='99d8cf99-41a5-490a-85e6-9dc8301c6cf9')


def parse_arguments():
    from argparse import ArgumentParser
    parser = ArgumentParser('file_uploader',
                            description='Will upload a file to a attachment property in a KE-chain server')
    parser.add_argument('--url', '-u', type=str, required=True,
                        default=URL,
                        help='Full url of the KE-chain server [Default: "%(default)s"]')
    parser.add_argument('--user', '-U', default=USERNAME, dest='username',
                        help='Username to access the KE-chain server[Default: "%(default)s"]')
    parser.add_argument('--pass', '--password', '-p', dest='password',
                        help='password of the user')
    parser.add_argument('--token', '-t',
                        help='token for the user (optional token API token authentication)')
    parser.add_argument('--scope', '-S', default=SCOPE_ID,
                        help='Scope in the product model [Default: "%(default)s"]')
    parser.add_argument('--part', '-P', required=True,
                        help='part name under which the property lives (quoted if the partname contains spaces')
    parser.add_argument('--property', '-A', type=str, required=True,
                        help='property name to Attach file to (quotes if the partname has spaces) '
                             '[Default: "%(default)s"]')
    parser.add_argument('--file', '-f', required=True,
                        help='Filename to upload to the node in the model in the repo')
    parser.add_argument('--logging', '-l', action='store_true',
                        help='Increase Verbosity logginglevel to Debug (Default INFO)')
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('--no-check-certificate', action='store_false', dest='check_certificate', default=True,
                        help='Do not check for valid SSL certificate (Default: will check!)')
    return parser.parse_args()


def upload_file_to_attachment_property(client, scope_id, part_name, property_name, filename, verbose=True):
    # find the property
    # check if attachment property
    # check if file exist
    # uploade the file
    # check result

    if not os.path.exists(filename):
        raise Exception("Filename '{}' could not be found, is it there?".format(filename))

    scope = client.scope(id=scope_id)
    target_part = scope.part(name=part_name, category="INSTANCE")
    target_property = target_part.property(property_name)

    if type(target_property) == AttachmentProperty:
        if verbose: sys.stdout.writelines('-- uploading {}\n'.format(filename))
        target_property.upload(filename)
        if verbose: sys.stdout.write('-- done')
    else:
        raise Exception("property '{}' is not of type AttachmentProperty, so could not upload file".
                        format(target_property))


def main():
    args = parse_arguments()
    if args.logging:
        sys.stdout.writelines(['%s : %s\n' % (k, v) for k, v in vars(args).items() if k not in ['password', 'token']])

    if args.logging:
        logging.basicConfig(level=logging.INFO)
        logging.getLogger('suds.client').setLevel(logging.DEBUG)
        logging.getLogger('suds.transport').setLevel(logging.DEBUG)
    try:
        client = Client(url=args.url, check_certificates=args.check_certificate)
    except LoginRequiredError as e:
        print(e)
        return 403

    if "token" in args and args.token:
        client.login(token=args.token)
    elif "username" in args and args.username and "password" in args and args.password:
        client.login(username=args.username, password=args.password)
    else:
        sys.stderr.write("\nError: Ensure that you provide both username and password or a single API auth token\n")
        return 1

    try:
        result = upload_file_to_attachment_property(client, args.scope, args.part, args.property, args.file,
                                                    args.logging)
    except Exception as e:
        print(e)
        return 1
    except NotFoundError as e:
        print(e)
        return 1
    except MultipleFoundError as e:
        print(e)
        return 3



    if result:
        msg = 'File "{}" is successfully uploaded to KE-chain'.format(args.file)
        return 0
    else:
        msg = 'Could not upload'
        return 1


if __name__ == "__main__":
    sys.exit(main())
