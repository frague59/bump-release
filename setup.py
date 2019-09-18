# -*- coding: utf-8 -*-
"""
setup for application

:creationdate: 13/09/2019 14:23
:moduleauthor: François GUÉRIN <fguerin@ville-tourcoing.fr>
:modulename: setup.py
"""
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="bump_release",
    version="0.5.2",
    author="François GUÉRIN",
    author_email="fguerin@ville-tourcoing.fr",
    description="Updates various version numbers for python projects",
    long_description=long_description,
    long_description_content_type="text/markdown",
    py_modules=["bump_release"],
    install_requires=[
        "Click",
        "PyYAML"
    ],
    entry_points="""
     [console_scripts]
     bump_release=bump_release:bump_release
    """,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
