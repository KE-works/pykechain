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
    print(">>> starting on {}".format(time.strftime("%c", time.gmtime(start))))
    print(f"--- arguments: {args}")
    print(f"--- keyword arguments: {kwargs}")
    print(f"--- local variables dict: {dir()}")
    pprint(f"--- environment: {os.environ}", width=120)
    pprint(f"--- platform details (uname): {platform.uname()}", width=120)
    pprint(f"--- python paths: {sys.path}", width=120)
    mark_1 = time.time()
    print(
        "<<< intermediate timing on {}, duration: {}".format(
            time.strftime("%c", time.gmtime(mark_1)), mark_1 - start
        )
    )
    print(
        "--- python pip packages installed \n{}".format(
            os.popen("pip freeze").readlines()
        )
    )
    try:
        import pykechain

        print(f"--- importing pykechain version: {pykechain.version}")
    except ImportError:
        print(
            r"/!\ pykechain is not installed, please install pykechain version 1.12 or later"
        )

    mark_2 = time.time()

    from envparse import env

    if (
        not env("KECHAIN_URL", None)
        or not env("KECHAIN_TOKEN", None)
        or not env("KECHAIN_SCOPE_ID", None)
    ):
        print(
            r"/!\ cannot interact using pykechain as environment variables KECHAIN_URL,"
            r" KECHAIN_TOKEN and "
            "KECHAIN_SCOPE_ID are not set"
        )
    else:
        project = pykechain.get_project()
        mark_3 = time.time()
        print(
            "--- retrieving project '{}' from kechain (url: {})".format(
                project.name, env("KECHAIN_URL")
            )
        )
        print(
            f"--- {len(project.activities())} activities, {len(project.parts())} parts"
        )
        print("--- retrieving as user: '{}".format(env("KECHAIN_USERNAME")))
        print(f"<<< interaction with ke-chain took: {mark_3-mark_2}s")

    end = time.time()
    print(
        "<<< ending on {}, duration: {}".format(
            time.strftime("%c", time.gmtime(end)), end - start
        )
    )


if __name__ == "__main__":
    sys.exit(main())
