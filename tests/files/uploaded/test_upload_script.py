#!/usr/bin/env python

"""
Debugging script returning the environment etc
"""

import os
import platform
import sys
import time
from pprint import pprint


def main(*args, **kwargs):
    start = time.time()
    foo, bar = "cow says", "moo!"
    print('>>> starting on {}'.format(time.strftime('%c', time.gmtime(start))))
    print('--- arguments: {}'.format(args))
    print('--- keyword arguments: {}'.format(kwargs))
    print('--- local variables dict: {}'.format(dir()))
    pprint('--- environment: {}'.format(os.environ), width=120)
    pprint('--- platform details (uname): {}'.format(platform.uname()), width=120)
    pprint('--- python paths: {}'.format(sys.path), width=120)
    mark_1 = time.time()
    print('<<< intermediate timing on {}, duration: {}'.format(time.strftime('%c', time.gmtime(mark_1)), mark_1 - start))
    print('--- python pip packages installed \n{}'.format(os.popen('pip freeze').readlines()))
    try:
        import pykechain
        print('--- importing pykechain version: {}'.format(pykechain.version))
    except ImportError:
        print('/!\ pykechain is not installed, please install pykechain version 1.12 or later')

    mark_2 = time.time()

    from envparse import env
    if not env('KECHAIN_URL', None) or not env('KECHAIN_TOKEN', None) or not env('KECHAIN_SCOPE_ID', None):
        print('/!\ cannot interact using pykechain as environment variables KECHAIN_URL, KECHAIN_TOKEN and '
              'KECHAIN_SCOPE_ID are not set')
    else:
        project = pykechain.get_project()
        mark_3 = time.time()
        print("--- retrieving project '{}' from kechain (url: {})".format(project.name, env('KECHAIN_URL')))
        print("--- {} activities, {} parts".format(len(project.activities()), len(project.parts())))
        print("--- retrieving as user: '{}".format(env('KECHAIN_USERNAME')))
        print("<<< interaction with ke-chain took: {}s".format(mark_3-mark_2))

    end = time.time()
    print('<<< ending on {}, duration: {}'.format(time.strftime('%c', time.gmtime(end)), end - start))


if __name__ == '__main__':
    sys.exit(main())
