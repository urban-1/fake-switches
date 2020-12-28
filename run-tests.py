#!/usr/bin/env python3

"""
Run all or some tests while handling the global reactor!
"""
import unittest
import argparse
import logging as lg
import sys
import os


from tests.util.global_reactor import ThreadedReactor

args = None


def parse_args():
    global args
    parser = argparse.ArgumentParser("Test-runner for fake-switch")
    parser.add_argument(
        "-t",
        "--tests",
        nargs="*",
    )
    parser.add_argument(
        "-v",
        "--verbosity",
        type=int,
        default=1,
        help="VErbosity [1-5], 5 is DEBUG",
    )

    return parser.parse_args()


def run_with_reactor(suite):
    global args
    thread = ThreadedReactor()
    thread.start()
    unittest.TextTestRunner(verbosity=args.verbosity).run(suite)
    thread.stop()
    lg.info("Joining reactor")
    thread.join()
    lg.info("Done")


def main():
    global args
    args = parse_args()


    if not args.tests:
        suite = unittest.TestLoader().discover(os.path.dirname(__file__)+'/tests')
        run_with_reactor(suite)
        return

    lg.info(' * Running requested tests')
    suite = unittest.TestSuite()

    # Load standard tests
    for t in args.tests:
        test = unittest.TestLoader().loadTestsFromName("tests." + t)
        suite.addTest(test)

    # Run
    run_with_reactor(suite)

if __name__ == "__main__":
    sys.exit(main())
