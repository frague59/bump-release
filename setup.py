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
    version="0.9.5",
    author="François GUÉRIN",
    author_email="fguerin@ville-tourcoing.fr",
    url="https://github.com/frague59/bump-release",
    description="Updates various version numbers for python projects",
    long_description=long_description,
    long_description_content_type="text/markdown",
    py_modules=["bump_release"],
    install_requires=["Click", "ruamel.yaml"],
    packages=setuptools.find_packages(),
    entry_points="""
     [console_scripts]
     bump_release=bump_release:bump_release
    """,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development",
    ],
    python_requires=">=3.7",
)
