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
import sys
from copy import deepcopy
from typing import Tuple, Optional, List, Any

__version__ = VERSION = "0.1.0"

ROOT = os.getcwd()

PACKAGES_FILES = ["package.json", "package-lock.json"]

# main
DEFAULT_MAIN_RE = r"^__version__\s*=\s*VERSION\s*=\s*['\"][.\d\w]+['\"]$"
DEFAULT_MAIN_TEMPLATE = '__version__ = VERSION = "{major}.{minor}.{release}"\n'

# Node
DEFAULT_NODE_KEY = "version"

# sonar
DEFAULT_SONAR_RE = r"^sonar.projectVersion=([.\d]+)$"
DEFAULT_SONAR_TEMPLATE = "sonar.projectVersion={major}.{minor}\n"

# Sphinx
DEFAULT_SPHINX_VERSION_FORMAT = 'version = "{major}.{minor}"\n'
DEFAULT_SPHINX_RELEASE_FORMAT = 'release = "{major}.{minor}.{release}"\n'
DEFAULT_SPHINX_VERSION_RE = r"^version\s+=\s+[\"']([.\d]+)[\"']$"
DEFAULT_SPHINX_RELEASE_RE = r"^release\s+=\s+[\"']([.\d]+)[\"']$"

LEVELS = (logging.FATAL, logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG)


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
    # Path is absolute
    if os.path.isabs(path):
        if os.path.isfile(path):
            return path
        else:
            raise UpdateException(
                "Path %s absolute path does not point to a real file. "
                "Please check your release.ini file" % path
            )

    # Path is relative
    abs_path = os.path.join(ROOT, path)
    logging.debug("normalize_file_path(%s) \nabs_path = %s", path, abs_path)
    if os.path.isfile(abs_path) or os.path.isdir(abs_path):
        logging.info("normalize_file_path(%s) %s exists", path, abs_path)
        return path

    raise UpdateException(
        "Path %s relative path does not point to a real file. "
        "Please check your release.ini file." % path
    )
# endregion Utilities


# region Updaters
def update_files(
    release_number: Tuple[str, str, str],
    config_path: Optional[str] = None,
    dry_run: bool = True,
):
    """
    Updates the files according to the release.ini file

    :param release_number: Number
    :param config_path: path to the release.ini config file
    :param dry_run: If `True`, no operation performed
    :return: 0 if no error...
    """
    logging.info("Current ROOT file: %s", ROOT)
    logging.info("Current config file: %s", config_path)
    parser = configparser.ConfigParser()
    parser.read(config_path)

    # Updates the main project (DJANGO_SETTINGS_MODULE file for django projects)
    ret = _update_main_file(
        parser=parser, release_number=release_number, dry_run=dry_run
    )
    if ret != 0:
        return ret

    ret = _update_node_package_json(
        parser=parser, release_number=release_number, dry_run=dry_run
    )
    if ret != 0:
        return ret

    # Updates sonar-scanner properties
    ret = _update_sonar_properties(
        parser=parser, release_number=release_number, dry_run=dry_run
    )
    if ret != 0:
        return ret

    # Updates sphinx file
    ret = _update_sphinx_conf(
        parser=parser, release_number=release_number, dry_run=dry_run
    )
    if ret != 0:
        return ret

    # Updates the release.ini file with the new release number
    ret = update_release_ini(
        path=config_path, release_number=release_number, dry_run=dry_run
    )
    if ret != 0:
        return ret

    return 0


def _update_main_file(
    parser: configparser.ConfigParser,
    release_number: Tuple[str, str, str],
    dry_run: bool = True,
) -> int:
    """
    Updates the main file: in django project, the settings/base.py file, else another file

    :param parser: config parser
    :param release_number: Release number tuple (major, minor, release)
    :param dry_run: If `True`, no operation performed
    :return: 0 if ok
    """
    try:
        main_path = parser.get("main_project", "path")
    except configparser.NoSectionError as nse:
        logging.warning("_update_main_file() No section provided: %s", nse)
        return 0
    except configparser.NoOptionError as noe:
        logging.warning("_update_main_file() No option provided: %s", noe)
        return 0

    main_pattern = parser.get("main_project", "re", fallback=DEFAULT_MAIN_RE)

    if main_path:
        try:
            _path = normalize_file_path(main_path)
            update_main_file(
                path=_path,
                pattern=main_pattern,
                release_number=release_number,
                dry_run=dry_run,
            )
        except UpdateException as ue:
            logging.fatal("update_files() Unable to update the main file: %s", ue)
            return 1
    return 0


def _update_node_package_json(
    parser: configparser.ConfigParser,
    release_number: Tuple[str, str, str],
    dry_run: bool = True,
) -> int:
    """
    Updates the node package file

    :param parser: config parser
    :param release_number: Release number tuple (major, minor, release)
    :param dry_run: If `True`, no operation performed
    :return: 0 if ok
    """
    # Updates the package.json and package-lock.json for node-based projects
    try:
        node_path = parser.get("node_module", "path")
    except configparser.NoSectionError as nse:
        logging.warning("_update_node_package_json() No section provided: %s", nse)
        return 0
    except configparser.NoOptionError as noe:
        logging.warning("_update_node_package_json() No option provided: %s", noe)
        return 0

    node_key = parser.get("node_module", "key", fallback=DEFAULT_NODE_KEY)

    if node_path:
        _path = normalize_file_path(node_path)
        try:
            update_node_packages(
                path=_path, release_number=release_number, key=node_key, dry_run=dry_run
            )
        except UpdateException as ue:
            logging.fatal("update_files() Unable to update the node file: %s", ue)
            return 2
    return 0


def _update_sonar_properties(
    parser: configparser.ConfigParser,
    release_number: Tuple[str, str, str],
    dry_run: bool = True,
) -> int:
    """
    Updates the sonar-project properties file

    :param parser: config parser
    :param release_number: Release number tuple (major, minor, release)
    :param dry_run: If `True`, no operation performed
    :return: 0 if ok
    """
    try:
        sonar_path = parser.get("sonar", "path")
    except configparser.NoSectionError as nse:
        logging.warning("_update_sonar_properties() No section provided: %s", nse)
        return 0
    except configparser.NoOptionError as noe:
        logging.warning("_update_sonar_properties() No option provided: %s", noe)
        return 0

    sonar_re = parser.get("sonar", "re", fallback=DEFAULT_SONAR_RE)
    if sonar_path and sonar_re:
        _path = normalize_file_path(sonar_path)
        try:
            update_sonar_properties(
                path=_path,
                pattern=sonar_re,
                release_number=release_number,
                dry_run=dry_run,
            )
        except UpdateException as ue:
            logging.fatal("update_files() Unable to update the sonar file: %s", ue)
            return 4
    return 0


def _update_sphinx_conf(
    parser: configparser.ConfigParser,
    release_number: Tuple[str, str, str],
    dry_run: bool = True,
):
    """
    Updates the sphinx conf.py file

    :param parser: config parser
    :param release_number: Release number tuple (major, minor, release)
    :param dry_run: If `True`, no operation performed
    :return: 0 if ok
    """
    try:
        sphinx_path = parser.get("docs", "path")
    except configparser.NoSectionError as nse:
        logging.warning("_update_sphinx_conf() No section provided: %s", nse)
        return 0
    except configparser.NoOptionError as noe:
        logging.warning("_update_sphinx_conf() No option provided: %s", noe)
        return 0

    sphinx_patterns = (
        parser.get("docs", "version_re", fallback=DEFAULT_SPHINX_VERSION_RE),
        parser.get("docs", "release_re", fallback=DEFAULT_SPHINX_RELEASE_RE),
    )

    if sphinx_path and sphinx_patterns:
        _path = normalize_file_path(sphinx_path)
        try:
            update_sphinx_conf(
                path=_path,
                patterns=sphinx_patterns,
                release_number=release_number,
                dry_run=dry_run,
            )
        except UpdateException as ue:
            logging.fatal("update_files() Unable to update the sphinx file: %s", ue)
            return 8
    return 0


def _update_file(
    path: str,
    pattern: str,
    version_format: str,
    release_number: Tuple[str, str, str],
    dry_run: bool = True,
):
    """
    Performs the **real** update of the `path` files, aka. replaces the row matched
    with `pattern` with `version_format` formatted according to `release_number`.

    :param path: path of the file to update
    :param pattern: regexp to replace
    :param version_format: version format
    :param release_number: Release number tuple (major, minor, release)
    :param dry_run: If `True`, no operation performed
    :return: Nothing
    """
    version_re = re.compile(pattern)

    old_row, new_row = None, None
    counter = 0
    with open(path, "r") as ifile:
        content_lines = ifile.readlines()
    new_content = deepcopy(content_lines)

    for counter, row in enumerate(content_lines):
        searched = version_re.search(row)
        if searched:
            logging.debug(
                "_update_file() a *MATCHING* row has been found:\n%d %s", counter, row
            )
            old_row = deepcopy(row)
            new_row = version_format.format(
                major=release_number[0],
                minor=release_number[1],
                release=release_number[2],
            )
            break

    if old_row and new_row:
        logging.info("_update_file() old_row:\n%s\nnew_row:\n%s", old_row, new_row)

    if dry_run:
        logging.info("_update_file() No operation performed, dry_run = %s", dry_run)
        return

    if new_row and counter:
        new_content[counter] = new_row
        with open(path, "w") as ofile:
            ofile.writelines(new_content)
        logging.info('_update_file() "%s" updated.', path)
        return
    raise UpdateException("An error has append on updating version")


def update_main_file(
    path: str, pattern: str, release_number: Tuple[str, str, str], dry_run: bool = True
):
    """
    Updates the main django settings file

    :param path: main file path
    :param pattern: regexp pattern to locate the version in file
    :param release_number: Release number tuple (major, minor, release)
    :param dry_run: If `True`, no operation performed
    :return: Nothing
    """

    _update_file(
        path=path,
        pattern=pattern,
        version_format=DEFAULT_MAIN_TEMPLATE,
        release_number=release_number,
        dry_run=dry_run,
    )


def update_node_packages(
    path: str,
    release_number: Tuple[str, str, str],
    key: str = DEFAULT_NODE_KEY,
    dry_run: bool = True,
):
    """
    Updates the package.json file

    :param path: Node root directory
    :param release_number: Release number
    :param dry_run: If `True`, no operation performed
    :param key: json dict key (default: "version")
    :return: Nothing
    """
    package_files = [
        os.path.join(ROOT, path, package_file) for package_file in PACKAGES_FILES
    ]

    for package_file in package_files:
        logging.info("update_node_packages() package_file = %s", package_file)
        try:
            with open(package_file, "r") as pf:
                package = json.loads(pf.read())
            new_package = deepcopy(package)
            new_package[key] = ".".join(release_number)
            updated = json.dumps(new_package, indent=4)
            if dry_run:
                logging.info(
                    "update_node_packages() No operation performed, dry_run = %s",
                    dry_run,
                )
                continue
            with open(package_file, "w") as pf:
                pf.write(updated)
                logging.info('update_node_packages() File "%s" updated.', package_file)

        except IOError as ioe:
            raise UpdateException(
                "update_node_packages() Unable to perform %s update:" % package_file,
                ioe,
            )


def update_sonar_properties(
    path: str, pattern: str, release_number: Tuple[str, str, str], dry_run: bool = True
):
    """
    Updates the sonar-project.properties file

    :param path: sonar-properties.ini file path
    :param pattern: RE pattern to locate the version string
    :param release_number: Release number as a tuple (<major>, <minor>, <release>)
    :param dry_run: If True, noop performed
    :return: Nothing
    """
    _update_file(
        path=path,
        pattern=pattern,
        version_format=DEFAULT_SONAR_TEMPLATE,
        release_number=release_number,
        dry_run=dry_run,
    )


def update_sphinx_conf(
    path: str,
    patterns: Tuple[str, str],
    release_number: Tuple[str, str, str],
    dry_run: bool = True,
):
    """
    Updates the sphinx conf.py file

    :param path: sphinx conf file path
    :param patterns: RE patterns to locate the version string
    :param release_number: Release number as a tuple (<major>, <minor>, <release>)
    :param dry_run: If `True`, no operation performed
    :return: Nothing
    """
    _update_file(
        path=path,
        pattern=patterns[0],
        version_format=DEFAULT_SPHINX_VERSION_FORMAT,
        release_number=release_number,
        dry_run=dry_run,
    )
    _update_file(
        path=path,
        pattern=patterns[1],
        version_format=DEFAULT_SPHINX_RELEASE_FORMAT,
        release_number=release_number,
        dry_run=dry_run,
    )


def update_release_ini(
    path: str, release_number: Tuple[str, str, str], dry_run: bool = False
):
    config = configparser.ConfigParser()
    config.read(path)
    previous_release = config.get("DEFAULT", "current_release")
    new_release = ".".join(release_number)
    if previous_release != new_release:
        logging.info(
            "update_release_ini() previous_release = %s / new_release = %s\n",
            previous_release,
            new_release,
        )
        if dry_run:
            logging.info(
                "update_release_ini() No operation performed, dry_run = %s", dry_run
            )
            return
        with open(path, "w") as cfg_file:
            config.set("DEFAULT", "current_release", new_release)
            config.write(cfg_file)
        logging.info('update_release_ini() "%s" updated.', path)
    return 0


# endregion Updaters


# region Launcher
def add_arguments(parser: argparse.ArgumentParser):
    """
    Adds args to parser

    :param parser: args parser
    :return: Updated args parser
    """
    parser.add_argument(action="store", dest="release", help="Target release number")

    parser.add_argument(
        "-v",
        "--verbose",
        action="store",
        dest="verbosity",
        default=3,
        help="Sets verbosity from 0 (quiet) to 4 (debug)",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        dest="debug",
        default=False,
        help="Sets debug mode: verbosity maxi",
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
        help="Path to the .ini config file",
    )
    return parser


def main(args: List[Any]):
    """
    Main launcher:

    + parses args
    + Checks for `release.ini` config file
    + Launch the updates

    :param args:
    :return:
    """
    global ROOT
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser = add_arguments(parser=parser)
    options = parser.parse_args(args)

    if options.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=options.verbosity)

    if os.path.isfile(options.config):
        ROOT = os.path.dirname(os.path.abspath(options.config))
        config_path = os.path.join(ROOT, options.config)
    else:
        logging.fatal("Ubable to locate the release file.")
        return -1

    release = split_release(options.release)
    return update_files(
        release_number=release, config_path=config_path, dry_run=options.dry_run
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
    # endregion Launcher
