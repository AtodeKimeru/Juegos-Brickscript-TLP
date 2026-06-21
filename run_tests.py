# -*- coding: utf-8 -*-
import importlib
import os
import sys


def _collect_tests(module):
    return [getattr(module, name) for name in dir(module) if name.startswith('test_')]


def main():
    root = os.path.dirname(os.path.abspath(__file__))
    if root not in sys.path:
        sys.path.insert(0, root)

    modules = [
        'tests.test_events',
        'tests.test_dispatcher',
        'tests.test_snake',
        'tests.test_tetris',
        'tests.test_compatibility',
    ]

    passed = 0
    for module_name in modules:
        module = importlib.import_module(module_name)
        for test in _collect_tests(module):
            test()
            print 'OK', test.__name__
            passed += 1

    print 'ALL PASSED (%d tests)' % passed


if __name__ == '__main__':
    main()
