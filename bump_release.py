#!/usr/bin/env python3
# -+- coding: utf-8 -+-
"""
Bumps a release according to a release.ini file

:author: François GUÉRIN <fguerin@ville-tourcoing.fr>
:date: 2019-01-21 08:36
"""
import argparse
import configparser
import json
import logging
import os
import re
from copy import deepcopy
from typing import Tuple, Optional

__version__ = VERSION = "0.1.0"

ROOT = os.getcwd()

DJANGO_SETTINGS_FILE = "src/events/settings/base.py"
SPHINX_CONF_FILE = "docs/source/conf.py"
SONAR_FILE = "sonar-project.properties"
PACKAGES_FILES = ["src/assets/packages.json", "src/assets/packages-lock.json"]

LEVELS = (
    logging.FATAL,
    logging.ERROR,
    logging.WARNING,
    logging.INFO,
    logging.DEBUG
)


# region Utilities
class UpdateException(Exception):
    """
    An error has append on updating version
    """


def split_release(version: str) -> Tuple[str, str, str]:
    """
    Splits the release number into a 3-uple

    :param version: version string
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


def normalize_file_path(path: str) -> str:
    """
    Checks if a file exists, determining if it is an absolute path or de relative one.

    :param path: Path to check
    :return: normalized absolute path
    """
    if os.path.isabs(path):
        if os.path.isfile(path):
            return path
        else:
            raise UpdateException("Path %s absolute path does not point to a real file. "
                                  "Please check your release.ini file" % path)
    if os.path.isfile(os.path.join(ROOT, path)):
        return path
    raise UpdateException("Path %s relative path does not point to a real file. "
                          "Please check your release.ini file." % path)


# endregion Utilities

# region Updaters
def update_files(
        release_number: Tuple[str, str, str],
        config_path: Optional[str] = None,
        dry_run: bool = True
):
    logging.info("Current config file: %s", config_path)
    parser = configparser.ConfigParser()
    parser.read(config_path)

    main_path = parser.get("DEFAULT", "main_project_file")
    if main_path:
        _path = normalize_file_path(main_path)
        update_main_file(path=_path, release_number=release_number, dry_run=dry_run)

    return 0


def update_main_file(
        path: str,
        pattern: str,
        release_number: Tuple[str, str, str],
        dry_run: bool
):
    """
    Updates the main django settings file

    :param path: main file path
    :param pattern: regexp pattern to locate the version in file
    :param release_number: Release number tuple (major, minor, release)
    :param dry_run: If `True`, no operation performed
    :return: Nothing
    """

    if not DJANGO_SETTINGS_FILE:
        print("update_main_file() no `DJANGO_SETTINGS_FILE` provided")

    major, minor, release = release_number

    version_re = re.compile(pattern)
    version_format = '__version__ = VERSION = "{major}.{minor}.{release}"\n'

    old_row, new_row = None, None
    counter = 0

    # Reads and copy the file content
    with open(path, "r") as ifile:
        content = ifile.readlines()
    new_content = deepcopy(content)

    for counter, row in enumerate(content):
        logging.debug(
            "update_main_file() a row has been found:\n%d %s", counter, row
        )
        searched = version_re.search(row)
        if searched:
            logging.debug(
                "update_main_file() a *MATCHING* row has been found:\n%d %s",
                counter,
                row,
            )
            old_row = deepcopy(row)
            new_row = version_format.format(major=major, minor=minor, release=release)
            break

    if old_row and new_row:
        logging.info(
            "update_main_file() old_row:\n%s\nnew_row:\n%s", old_row, new_row
        )

    if not dry_run and new_row and counter:
        new_content[counter] = new_row

        with open(os.path.join(ROOT, DJANGO_SETTINGS_FILE), "w") as ofile:
            ofile.writelines(new_content)
        logging.info('update_main_file() "%s" updated.', DJANGO_SETTINGS_FILE)
        return

    raise UpdateException("An error has append on updating version")


def update_packages_json(major: str, minor: str, release: str, dry_run: bool):
    """
    Updates the packages.json file

    :param major: Major version
    :param minor: Minor version
    :param release: Release number
    :param dry_run: If `True`, no operation performed
    :return: Nothing
    """
    if not PACKAGES_FILES:
        print("update_packages_json() no `PACKAGES_FILES` provided")
        return

    if isinstance(PACKAGES_FILES, str):
        _PACKAGES_FILES = [PACKAGES_FILES]
    else:
        _PACKAGES_FILES = deepcopy(PACKAGES_FILES)

    for file in _PACKAGES_FILES:
        packages_file = os.path.join(ROOT, file)
        logging.info("update_packages_json() packages_file = %s", packages_file)
        try:
            with open(packages_file, "rw") as pf:
                packages = json.loads(pf.read())
                packages["version"] = ".".join([major, minor, release])
                updated = json.dumps(packages, indent=4)
                if not dry_run:
                    pf.write(updated)
        except IOError as ioe:
            raise UpdateException("Unable to perform packages[-lock].json update:", ioe)


def update_sphinx_conf(major: str, minor: str, release: str, dry_run: bool):
    """
    Updates the sphinx conf.py file

    :param major: Major version
    :param minor: Minor version
    :param release: Release number
    :param dry_run: If `True`, no operation performed
    :return: Nothing
    """
    if not SPHINX_CONF_FILE:
        print("update_sphinx_conf() no `SPHINX_CONF_FILE` provided")
        return

    version_re = re.compile(r"^version\s+=\s+[\"']([.\d]+)[\"']$")
    release_re = re.compile(r"^release\s+=\s+[\"']([.\d]+)[\"']$")

    version_format = 'version = "{major}.{minor}"\n'
    release_format = 'release = "{major}.{minor}.{release}"\n'

    old_version_row, old_release_row = None, None
    new_version_row, new_release_row = None, None

    # Reads and copy the file content
    with open(os.path.join(ROOT, SPHINX_CONF_FILE), "r") as ifile:
        content = ifile.readlines()
    new_content = deepcopy(content)

    # parse files
    counter_release, counter_version = 0, 0
    for counter, row in enumerate(content):
        # Searches for the "version" row
        version_searched = version_re.search(row)
        if version_searched:
            counter_version = counter
            old_version_row = deepcopy(row)
            new_version_row = version_format.format(major=major, minor=minor)
            continue

        # Searches for the "release" row
        release_searched = release_re.search(row)
        if release_searched:
            counter_release = counter
            old_release_row = deepcopy(row)
            new_release_row = release_format.format(
                major=major, minor=minor, release=release
            )
            continue

        if old_version_row and old_release_row and new_version_row and new_release_row:
            break

    if old_version_row and old_release_row:
        logging.info(
            "update_sphinx_conf() old_version_row:\n%s\nnew_version_row:\n%s",
            old_version_row,
            new_version_row,
        )

    if not dry_run and counter_version and counter_release:
        new_content[counter_version] = new_version_row
        new_content[counter_release] = new_release_row

        with open(os.path.join(ROOT, SPHINX_CONF_FILE), "w") as ofile:
            ofile.writelines(new_content)
        logging.info('update_sphinx_conf() "%s" updated.', SPHINX_CONF_FILE)
        return

    raise UpdateException("An error has append on updating version")


def update_sonar_properties(major: str, minor: str, release: str, dry_run: bool):
    """
    Updates the sonar-project.properties file

    :param major: Major version
    :param minor: Minor version
    :param release: Release number
    :param dry_run: If `True`, no operation performed
    :return: Nothing
    """
    if not SONAR_FILE:
        print("update_sonar_properties() no `SONAR_FILE` provided")
        return

    version_re = re.compile(r"^sonar.projectVersion=([.\d]+)$")
    version_format = "sonar.projectVersion={major}.{minor}\n"

    old_version_row, new_version_row = None, None

    with open(os.path.join(ROOT, SONAR_FILE), "r") as ifile:
        content = ifile.readlines()

    new_content = deepcopy(content)
    counter = 0

    for counter, row in enumerate(content):
        version_searched = version_re.search(row)
        if version_searched:
            old_version_row = deepcopy(row)
            new_version_row = version_format.format(major=major, minor=minor)
            break

    if old_version_row:
        logging.info(
            "update_sonar_properties() old_version_row:\n%s\nnew_version_row:\n%s",
            old_version_row,
            new_version_row,
        )

    if not dry_run:
        new_content[counter] = new_version_row
        with open(os.path.join(ROOT, SONAR_FILE), "w") as ofile:
            ofile.writelines(new_content)
        logging.info('update_sonar_properties() "%s" updated.', SONAR_FILE)
        return

    raise UpdateException("An error has append on updating version")


# endregion Updaters


# region Launcher
def add_arguments(parser: argparse.ArgumentParser):
    parser.add_argument(action="store", dest="release", help="Target release number")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store",
        dest="verbosity",
        default=3,
        help="Sets verbosity from 0 (quiet) to 4 (very verbose)",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        dest="dry_run",
        default=False,
        help="Does not performs anything, displays the updates",
    )
    parser.add_argument(
        "-c",
        "--config",
        action="store",
        dest="config",
        default="./release.ini",
        help="Path to the .ini config file"
    )
    return parser


def main(args: List[Any]):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser = add_arguments(parser=parser)
    options = parser.parse_args(args)

    if options.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=options.verbosity)

    config_path = os.path.join(ROOT, options.config)
    if not os.path.isfile(config_path):
        print("ERROR: Unable to find the config path: ", config_path)
        return 1

    release = split_release(options.release)
    return update_files(release_number=release, config_path=config_path)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:])
    # endregion Launcher
