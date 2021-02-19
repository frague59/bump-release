"""
Update release numbers in various places, according to a release.ini file places at the project root
"""
import configparser
import logging
import sys
from configparser import ConfigParser
from pathlib import Path
from typing import Optional, Tuple

import click

from bump_release import helpers
from bump_release.helpers import split_version

# region Globals
__version__ = VERSION = "0.9.5"
RELEASE_FILE: Optional[Path] = None
RELEASE_CONFIG: Optional[ConfigParser] = None
# endregion Globals


@click.command()
@click.option(
    "-r",
    "--release-file",
    "release_file",
    help="Release file path, default `./release.ini`",
)
@click.option(
    "-n",
    "--dry-run",
    "dry_run",
    is_flag=True,
    help="If set, no operation are performed on files",
    default=False,
)
@click.option(
    "-d",
    "--debug",
    "debug",
    is_flag=True,
    help="If set, more traces are printed for users",
    default=False,
)
@click.version_option(version=__version__)
@click.argument("release")
def bump_release(
    release: str,
    release_file: Optional[str] = None,
    dry_run: bool = False,
    debug: bool = False,
) -> int:
    """
    Updates the files according to the release.ini file

    :param release: Version number, as "X.X.X"
    :param release_file: path to the release.ini config file
    :param dry_run: If `True`, no operation performed
    :param debug: If `True`, more traces !
    :return: 0 if no error...
    """
    # Loads the release.ini file
    global RELEASE_CONFIG, RELEASE_FILE

    if release_file is None:
        RELEASE_FILE = Path.cwd() / "release.ini"
    else:
        RELEASE_FILE = Path(release_file)

    if not RELEASE_FILE.exists():
        print(f"Unable to find release.ini file in the current directory {Path.cwd()}", file=sys.stderr)
        return 1

    RELEASE_CONFIG = helpers.load_release_file(release_file=RELEASE_FILE)
    try:
        return process_update(release_file=RELEASE_FILE, release=release, dry_run=dry_run, debug=debug)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2


def process_update(release_file: Path, release: str, dry_run: bool, debug: bool = False) -> int:
    version = split_version(release)

    # Initialize the logging
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # region Updates the main project (DJANGO_SETTINGS_MODULE file for django projects, __init__.py file...)
    try:
        new_row = update_main_file(version=version, dry_run=dry_run)
        if new_row is not None:
            logging.debug(f"process_update() `main_project`: new_row = {new_row.strip()}")
    except helpers.NothingToDoException as e:
        logging.warning(f"process_update() No release section for `main_project`: {e}")
    # endregion

    # region Updates sonar-scanner properties
    try:
        new_row = update_sonar_properties(version=version, dry_run=dry_run)
        if new_row is not None:
            logging.debug(f"process_update() `sonar`: new_row = {new_row.strip()}")
    except helpers.NothingToDoException as e:
        logging.warning(f"process_update() No release section for `sonar`: {e}")
    # endregion

    # region Updates setup.py file
    try:
        new_row = update_setup_file(version=version, dry_run=dry_run)
        if new_row is not None:
            logging.debug(f"process_update() `setup`: new_row = {new_row.strip()}")
    except helpers.NothingToDoException as e:
        logging.warning(f"process_update() No release section for `setup`: {e}")
    # endregion

    # region Updates sphinx file
    try:
        new_row = update_docs_conf(version=version, dry_run=dry_run)
        if new_row is not None:
            logging.debug(f"process_update() `docs`: new_row = {new_row.strip()}")
    except helpers.NothingToDoException as e:
        logging.warning(f"process_update() No release section for `docs`: {e}")
    # endregion

    # region Updates node packages file
    try:
        new_row = update_node_package(version=version, dry_run=dry_run)
        if new_row is not None:
            logging.debug(
                f"process_update() `node`: new_row = {new_row}",
            )
    except helpers.NothingToDoException as e:
        logging.warning(f"process_update() No release section for `node`: {e}")
    # endregion

    # region Updates YAML file
    try:
        new_row = update_ansible_vars(version=version, dry_run=dry_run)
        if new_row is not None:
            logging.debug(f"process_update() `ansible`: new_row = {new_row.strip()}")
    except helpers.NothingToDoException as e:
        logging.warning(f"process_update() No release section for `ansible`: {e}")
    # endregion

    # region Updates the release.ini file with the new release number
    new_row = update_release_ini(path=release_file, version=version, dry_run=dry_run)
    if new_row is not None:
        logging.warning(f"process_update() `release.ini`: new_row = {new_row.strip()}")
    # endregion

    return 0


def update_main_file(version: Tuple[str, str, str], dry_run: bool = True) -> Optional[str]:
    """
    Updates the main django settings file, or a python script with

    :param version: Release number tuple (major, minor, release)
    :param dry_run: If `True`, no operation performed
    :return: changed string
    """
    assert RELEASE_CONFIG is not None
    if not RELEASE_CONFIG.has_section("main_project"):
        raise helpers.NothingToDoException("No `main_project` section in release.ini file")

    try:
        _path = RELEASE_CONFIG["main_project"].get("path")
        if _path is None:
            raise helpers.NothingToDoException("No action to perform for main project: No path provided.")
        path = Path(_path)
        pattern = RELEASE_CONFIG["main_project"].get("pattern") or helpers.MAIN_PROJECT_PATTERN
        pattern = pattern.strip('"')
        template = RELEASE_CONFIG["main_project"].get("template") or helpers.MAIN_PROJECT_TEMPLATE
        template = template.strip('"')
    except configparser.Error as e:
        raise helpers.NothingToDoException("Unable to update main project file", e)
    return helpers.update_file(path=path, pattern=pattern, template=template, version=version, dry_run=dry_run)


def update_setup_file(version: Tuple[str, str, str], dry_run: bool = False) -> Optional[str]:
    """
    Updates the setup.py file

    :param version: Release number tuple (major, minor, release)
    :param dry_run: If `True`, no operation performed
    :return: changed string
    """
    assert RELEASE_CONFIG is not None
    if not RELEASE_CONFIG.has_section("setup"):
        raise helpers.NothingToDoException("No `setup` section in release.ini file")

    try:
        _path = RELEASE_CONFIG["setup"].get("path")
        path = Path(_path)
        pattern = RELEASE_CONFIG["setup"].get("pattern") or helpers.SETUP_PATTERN
        pattern = pattern.strip('"')
        template = RELEASE_CONFIG["setup"].get("template") or helpers.SETUP_TEMPLATE
        template = template.strip('"')

    except configparser.Error as e:
        raise helpers.NothingToDoException("No action to perform for setup file", e)
    return helpers.update_file(path=path, pattern=pattern, template=template, version=version, dry_run=dry_run)


def update_sonar_properties(version: Tuple[str, str, str], dry_run: bool = False) -> Optional[str]:
    """
    Updates the sonar-project.properties file with the new release number

    :param version: Release number tuple (major, minor, release)
    :param dry_run: If `True`, no operation performed
    :return: changed string
    """
    assert RELEASE_CONFIG is not None
    if not RELEASE_CONFIG.has_section("sonar"):
        raise helpers.NothingToDoException("No `sonar` section in release.ini file")

    try:
        _path = RELEASE_CONFIG["sonar"].get("path")
        path = Path(_path)
        pattern = RELEASE_CONFIG["sonar"].get("pattern") or helpers.SONAR_PATTERN
        pattern = pattern.strip('"')
        template = RELEASE_CONFIG["sonar"].get("template") or helpers.SONAR_TEMPLATE
        template = template.strip('"')
    except configparser.Error as e:
        raise helpers.NothingToDoException("No action to perform for sonar file", e)
    return helpers.update_file(path=path, pattern=pattern, template=template, version=version, dry_run=dry_run)


def update_docs_conf(version: Tuple[str, str, str], dry_run: bool = False) -> Optional[str]:
    """
    Updates the Sphinx conf.py file with the new release number

    :param version: Release number tuple (major, minor, release)
    :param dry_run: If `True`, no operation performed
    :return: changed string
    """
    assert RELEASE_CONFIG is not None
    if not RELEASE_CONFIG.has_section("docs"):
        raise helpers.NothingToDoException("No `docs` section in release.ini file")

    try:
        _path = RELEASE_CONFIG["docs"].get("path")
        path = Path(_path)

        pattern_release = RELEASE_CONFIG["docs"].get("pattern_release") or helpers.DOCS_RELEASE_PATTERN
        pattern_release = pattern_release.strip('"')

        template_release = RELEASE_CONFIG["docs"].get("template_release") or helpers.DOCS_RELEASE_FORMAT
        template_release = template_release.strip('"')

        pattern_version = RELEASE_CONFIG["docs"].get("pattern_version") or helpers.DOCS_VERSION_PATTERN
        pattern_version = pattern_version.strip('"')

        template_version = RELEASE_CONFIG["docs"].get("template_version") or helpers.DOCS_VERSION_FORMAT
        template_version = pattern_version.strip('"')
    except configparser.Error as e:
        raise helpers.NothingToDoException("No action to perform for docs file", e)

    update_release = helpers.update_file(
        path=path,
        pattern=pattern_release,
        template=template_release,
        version=version,
        dry_run=dry_run,
    )
    update_version = helpers.update_file(
        path=path,
        pattern=pattern_version,
        template=template_version,
        version=version,
        dry_run=dry_run,
    )
    return str(update_release) + str(update_version)


def update_node_package(version: Tuple[str, str, str], dry_run: bool = False) -> Optional[str]:
    """
    Updates the nodejs package file with the new release number

    :param version: Release number tuple (major, minor, release)
    :param dry_run: If `True`, no operation performed
    :return: changed string
    """
    assert RELEASE_CONFIG is not None
    try:
        path = Path(RELEASE_CONFIG.get("node", "path"))
        key = RELEASE_CONFIG.get("node", "key", fallback=helpers.NODE_KEY)  # noqa
    except configparser.Error as e:
        raise helpers.NothingToDoException("No action to perform for node packages file", e)
    return helpers.update_node_packages(path=path, version=version, key=key, dry_run=dry_run)


def update_ansible_vars(version: Tuple[str, str, str], dry_run: bool = False) -> Optional[str]:
    """
    Updates the ansible project variables file with the new release number

    :param version: Release number tuple (major, minor, release)
    :param dry_run: If `True`, no operation performed
    :return: changed string
    """
    assert RELEASE_CONFIG is not None
    try:
        path = Path(RELEASE_CONFIG.get("ansible", "path"))
        key = RELEASE_CONFIG.get("ansible", "key", fallback=helpers.ANSIBLE_KEY)  # noqa
    except configparser.Error as e:
        raise helpers.NothingToDoException("No action to perform for ansible file", e)
    return helpers.updates_yaml_file(path=path, version=version, key=key, dry_run=dry_run)


def update_release_ini(path: Path, version: Tuple[str, str, str], dry_run: bool = False) -> Optional[str]:
    """
    Updates the release.ini file with the new release number

    :param path: Release file path
    :param version: release number, as (<major>, <minor>, <release>)
    :param dry_run: If `True`, the operation WILL NOT be performed
    :return: Updated lines
    """
    return helpers.update_file(
        path=path,
        pattern=helpers.RELEASE_INI_PATTERN,
        template=helpers.RELEASE_INI_TEMPLATE,
        version=version,
        dry_run=dry_run,
    )
