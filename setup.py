# -*- coding: utf-8 -*-
"""
setup for application

:creationdate: 13/09/2019 14:23
:moduleauthor: François GUÉRIN <fguerin@ville-tourcoing.fr>
:modulename: setup.py
"""
from setuptools import setup

setup(
    name="bump_release",
    version="0.1.0",
    py_modules=["bump_release"],
    install_requires=[
        "Click",
        "pyyaml"
    ],
    entry_points="""
     [console_scripts]
     bump_release=bump_release:bump_release
    """
)
