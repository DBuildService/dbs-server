#!/usr/bin/env python3
# encoding: utf-8

from setuptools import setup, find_packages

setup(
    name         = "dbs",
    version      = '0.2',
    description  = "DBS Build Service",
    author       = "Matej Stuchlik",
    author_email = "mstuchli@redhat.com",
    url          = "https://github.com/sYnfo/dbs",
    packages     = find_packages(),
    include_package_data = True,
)
