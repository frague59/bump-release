# -*- coding: utf-8 -*-
"""
helpers for :mod:`bump_release` application

:creationdate: 16/09/2019 08:18
:moduleauthor: François GUÉRIN <fguerin@ville-tourcoing.fr>
:modulename: bump_release.helpers

"""
import logging
import os
import re
from copy import deepcopy
from pathlib import Path
from typing import Tuple, Union
import configparser
import yaml
import json

__author__ = 'fguerin'
logger = logging.getLogger('bump_release.helpers')

RELEASE_CONFIG = None
BASE_DIR = os.getcwd()
# region Constants
# Node (JSON value update)
NODE_KEY = "version"
NODE_PACKAGE_FILE = "package.json"

# main (re search and replace)
MAIN_PROJECT_PATTERN = r"^__version__\s*=\s*VERSION\s*=\s*['\"][.\d\w]+['\"]$"
MAIN_PROJECT_TEMPLATE = '__version__ = VERSION = "{major}.{minor}.{release}"\n'

# Ansible yaml key
ANSIBLE_KEY = "git.branch"

# sonar (re search and replace)
SONAR_PATTERN = r"^sonar.projectVersion=([.\d]+)$"
SONAR_TEMPLATE = "sonar.projectVersion={major}.{minor}\n"

# Sphinx (re search and replace)
DOCS_VERSION_FORMAT = 'version = "{major}.{minor}"\n'
DOCS_RELEASE_FORMAT = 'release = "{major}.{minor}.{release}"\n'
DOCS_VERSION_PATTERN = r"^version\s+=\s+[\"']([.\d]+)[\"']$"
DOCS_RELEASE_PATTERN = r"^release\s+=\s+[\"']([.\d]+)[\"']$"


# endregion Constants

def load_release_file(release_file: Union[Path, str]) -> configparser.ConfigParser:
    """
    Loads the release file and stores the config into the global :attr:`RELEASE_CONFIG`

    :param release_file: Path to the release file
    :return: Loaded config
    """
    global RELEASE_CONFIG
    RELEASE_CONFIG = configparser.ConfigParser()
    RELEASE_CONFIG.read(release_file)
    return RELEASE_CONFIG


def split_version(version: str) -> Tuple[str, str, str]:
    """
    Splits the release number into a 3-uple

    :param version: version string
    :return: <major>, <minor>, <release>
    """
    try:
        major, minor, release = version.split(".")
    except ValueError:
        logging.fatal(
            'Version number "%s" does not respect the <MAJOR>.<MINOR>.<RELEASE> format.',
            version,
        )
        raise
    else:
        return major, minor, release


def update_file(path: str, pattern: str, template: str, release_number: Tuple[str, str, str],
                dry_run: bool = False) -> str:
    """
    Performs the **real** update of the `path` files, aka. replaces the row matched
    with `pattern` with `version_format` formatted according to `version`.

    :param path: path of the file to update
    :param pattern: regexp to replace
    :param template: version format
    :param release_number: Release number tuple (major, minor, release)
    :param dry_run: If `True`, no operation performed
    :return: New row
    """
    version_re = re.compile(pattern)
    major, minor, release = release_number

    old_row, new_row = None, None
    counter = None
    with open(path, "r") as ifile:
        content_lines = ifile.readlines()
    new_content = deepcopy(content_lines)

    for counter, row in enumerate(content_lines):
        searched = version_re.search(row)
        if searched:
            logging.debug("update_file() a *MATCHING* row has been found:\n%d %s", counter, row)
            old_row = deepcopy(row)
            new_row = template.format(major=major, minor=minor, release=release)
            break

    if old_row and new_row:
        logging.info("update_file() old_row:\n%s\nnew_row:\n%s", old_row, new_row)

    if dry_run:
        logging.info("update_file() No operation performed, dry_run = %s", dry_run)
        return new_row

    if new_row and counter is not None:
        new_content[counter] = new_row
        with open(path, "w") as output_file:
            output_file.writelines(new_content)
        logging.info('update_file() "%s" updated.', path)
        return new_row

    raise UpdateException("An error has append on updating version")


def update_node_packages(
        path: str,
        version: Tuple[str, str, str],
        key: str = NODE_KEY,
        dry_run: bool = False,
):
    """
    Updates the package.json file

    :param path: Node root directory
    :param version: Release number
    :param dry_run: If `True`, no operation performed
    :param key: json dict key (default: "version")
    :return: Nothing
    """
    try:
        with open(path, "r") as package_file:
            package = json.loads(package_file.read())
        new_package = deepcopy(package)
        new_package[key] = ".".join(version)
        updated = json.dumps(new_package, indent=4)
        if not dry_run:
            with open(path, "w") as package_file:
                package_file.write(updated)
        return updated
    except IOError as ioe:
        raise UpdateException(
            "update_node_packages() Unable to perform %s update:" % package_file,
            ioe,
        )


def updates_yml_file(
        path: str,
        version: Tuple[str, str, str],
        key: str = NODE_KEY,
        dry_run: bool = False,
) -> str:
    splited_key = key.split(".")
    full_version = ".".join(version)
    with open(path, "r") as vars_file:
        document = yaml.load(vars_file, Loader=yaml.FullLoader)
    node = document
    for _key in splited_key:
        if _key == splited_key[-1] and not dry_run:
            node.update({_key: full_version})
        node = node.get(_key)
    logger.debug("updates_yml_file() node value = %s", node)
    new_content = yaml.dump(document)
    if not dry_run:
        with open(path, "w") as vars_file:
            vars_file.write(new_content)
    return new_content


class UpdateException(Exception):
    """
    An error has occurred during the version updating
    """


class NothingToDoException(UpdateException):
    """
    An error has occurred during the version updating: Nothing to do...
    """