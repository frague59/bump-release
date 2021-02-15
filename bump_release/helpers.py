"""
helpers for :mod:`bump_release` application

:creationdate: 16/09/2019 08:18
:moduleauthor: François GUÉRIN <fguerin@ville-tourcoing.fr>
:modulename: bump_release.helpers

"""
import configparser
import json
import logging
import os
import re
from copy import deepcopy
from pathlib import Path
from typing import Optional, Tuple, Union

from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO

__author__ = "fguerin"

RELEASE_CONFIG = None
BASE_DIR = os.getcwd()
# region Constants
# Node (JSON value update)
NODE_KEY = "version"
NODE_PACKAGE_FILE = "package.json"

# main (re search and replace)
MAIN_PROJECT_PATTERN = r"^__version__\s*=\s*VERSION\s*=\s*['\"][.\d\w]+['\"]$"
MAIN_PROJECT_TEMPLATE = '__version__ = VERSION = "{major}.{minor}.{release}"'

# Ansible yaml key
ANSIBLE_KEY = "git.version"

# sonar (re search and replace)
SONAR_PATTERN = r"^sonar.projectVersion=([.\d]+)$"
SONAR_TEMPLATE = "sonar.projectVersion={major}.{minor}"

# setup.py file
SETUP_PATTERN = r"^\s*version=['\"]([.\d\w]+)['\"],$"
SETUP_TEMPLATE = '    version="{major}.{minor}.{release}",'


# Sphinx (re search and replace)
DOCS_VERSION_PATTERN = r"^version\s*=\s*[\"']([.\d\w]+)[\"']$"
DOCS_RELEASE_PATTERN = r"^release\s*=\s*[\"']([.\d\w]+)[\"']$"
DOCS_VERSION_FORMAT = 'version = "{major}.{minor}"'
DOCS_RELEASE_FORMAT = 'release = "{major}.{minor}.{release}"'

RELEASE_INI_PATTERN = r"^current_release\s*=\s*['\"]?([.\d\w]+)['\"]?$"
RELEASE_INI_TEMPLATE = "current_release = {major}.{minor}.{release}"


# endregion Constants


def load_release_file(release_file: Union[Path, str]) -> configparser.ConfigParser:
    """
    Loads the release file

    :param release_file: Path to the release file
    :return: Loaded config
    """
    release_config = configparser.ConfigParser()
    release_config.read(release_file)
    return release_config


def split_version(version: str) -> Tuple[str, str, str]:
    """
    Splits the release number into a 3-uple

    :param version: release string
    :return: <major>, <minor>, <release>
    """
    try:
        major, minor, release = version.split(".")
    except ValueError:
        logging.fatal(f'Version number "{version}" does not respect the <MAJOR>.<MINOR>.<RELEASE> format.')
        raise
    else:
        return major, minor, release


def update_file(
    path: Path,
    pattern: str,
    template: str,
    version: Tuple[str, str, str],
    dry_run: Optional[bool] = False,
) -> Optional[str]:
    """
    Performs the **real** update of the `path` files, aka. replaces the row matched
    with `pattern` with `version_format` formatted according to `release`.

    :param path: path of the file to update
    :param pattern: regexp to replace
    :param template: release format
    :param version: Release number tuple (major, minor, release)
    :param dry_run: If `True`, no operation performed
    :return: New row
    """
    version_re = re.compile(pattern)
    major, minor, release = version

    old_row, new_row = None, None
    counter = None
    with path.open(mode="r") as ifile:
        content_lines = ifile.readlines()
    new_content = deepcopy(content_lines)

    for counter, row in enumerate(content_lines):
        searched = version_re.search(row)
        if searched:
            logging.debug(f"update_file({path}) a *MATCHING* row has been found:\n{counter} {row.strip()}")
            old_row = deepcopy(row)
            new_row = template.format(major=major, minor=minor, release=release)
            if old_row.endswith("\r\n"):
                new_row += "\r\n"
            elif old_row.endswith("\r"):
                new_row += "\r"
            elif old_row.endswith("\n"):
                new_row += "\n"
            break

    if old_row and new_row:
        logging.info(f"update_file({path}) old_row:\n{old_row.strip()}\nnew_row:\n{new_row.strip()}")

    if dry_run:
        logging.info(
            f"update_file({path}) No operation performed, dry_run = {dry_run}",
        )
        return new_row

    if new_row and counter is not None:
        new_content[counter] = new_row
        with path.open(mode="w") as output_file:
            output_file.writelines(new_content)
        logging.info(f"update_file({path}) File updated.")
        return new_row

    raise UpdateException(f"An error has append on updating release for file {path}")


def update_node_packages(
    path: Path,
    version: Tuple[str, str, str],
    key: str = NODE_KEY,
    dry_run: bool = False,
):
    """
    Updates the package.json file

    :param path: Node root directory
    :param version: Release number
    :param dry_run: If `True`, no operation performed
    :param key: json dict key (default: "release")
    :return: Nothing
    """
    try:
        with path.open(mode="r") as package_file:
            package = json.loads(package_file.read())
        new_package = deepcopy(package)
        new_package[key] = ".".join(version)
        updated = json.dumps(new_package, indent=4)
        if not dry_run:
            with path.open(mode="w") as package_file:
                package_file.write(updated)
        return updated
    except IOError as ioe:
        raise UpdateException(f"update_node_packages() Unable to perform {package_file} update: {ioe}")


class MyYAML(YAML):
    """
    Wrapper around ruamel.yaml to output directly strings
    """

    def dump(self, data, stream=None, **kw):
        inefficient = False
        if stream is None:
            inefficient = True
            stream = StringIO()
        YAML.dump(self, data, stream, **kw)
        if inefficient:
            return stream.getvalue()


def updates_yaml_file(
    path: Path,
    version: Tuple[str, str, str],
    key: str = ANSIBLE_KEY,
    dry_run: bool = False,
) -> str:
    """
    Replaces the version number in a YAML file, aka. ansible vars files

    :param path: Path to the yaml file
    :param version: New version to apply, as a tuple (major, minor, release)
    :param key: key in the files, as xxx.yyy
    :param dry_run: If True, no action is performed
    :returns: new file content
    """
    splited_key = key.split(".")
    full_version = ".".join(version)
    yaml = MyYAML()
    with path.open(mode="r") as vars_file:
        document = yaml.load(vars_file)
    node = document
    for _key in splited_key:
        if _key == splited_key[-1] and not dry_run:
            node.update({_key: full_version})
        node = node.get(_key)
    logging.debug(f"updates_yml_file({vars_file}) node value = {node}")
    new_content = yaml.dump(document)
    if not dry_run:
        with path.open(mode="w") as vars_file:
            vars_file.write(new_content)
    return new_content


class UpdateException(Exception):
    """
    An error has occurred during the release updating
    """


class NothingToDoException(UpdateException):
    """
    An error has occurred during the release updating: Nothing to do...
    """
