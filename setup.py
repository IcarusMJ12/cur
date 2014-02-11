#!/usr/bin/env python

from setuptools import setup

setup(name = 'cur',
        version = '0.1.1',
        description = 'code copypasta detector',
        author = 'Igor Kaplounenko',
        author_email = 'igor@bittorrent.com',
        license = 'BSD',
        keywords = 'copypasta',
        provides = ['cur'],
        requires = ['termcolor (>=1.0)'],
        py_modules = ['strie'],
        scripts = ['cur.py'],
        long_description = open('README').read()
)
