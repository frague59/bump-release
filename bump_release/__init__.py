# coding: utf-8
"""
Update release numbers in various places, according to a release.ini file places at the project root
"""
import os

import click
import configparser
import logging
from io import StringIO
from pathlib import Path
from typing import Tuple, Optional
from bump_release import helpers

logger = logging.getLogger("bump_release")


# region Constants
__version__ = VERSION = "0.3.0"
DEBUG = True
RELEASE_CONFIG = None
# endregion Constants


@click.command()
@click.option("-r", "--release-file", "release_file", help="Release file path, default `./release.ini`")
@click.option("-n", "--dry-run", "dry_run", is_flag=True, help="If set, no operation are performed on files")
@click.version_option(version=__version__)
@click.argument("release")
def bump_release(
        release: Tuple[str, str, str],
        release_file: Optional[str] = None,
        dry_run: bool = True,
):
    """
    Updates the files according to the release.ini file

    :param release: Version number, as "X.X.X"
    :param release_file: path to the release.ini config file
    :param dry_run: If `True`, no operation performed
    :return: 0 if no error...
    """
    # Loads the release.ini file
    global RELEASE_CONFIG

    if release_file is None:
        release_file = Path(os.getcwd()) / "release.ini"
    RELEASE_CONFIG = helpers.load_release_file(release_file=release_file)
    version = helpers.split_version(release)

    # region Updates the main project (DJANGO_SETTINGS_MODULE file for django projects, __init__.py file...)
    try:
        new_row = update_main_file(version=version, dry_run=dry_run)
        logger.debug("bump_release() `main_project`: new_row = %s", new_row)
    except helpers.NothingToDoException as e:
        logger.info("No release section for `main_project`: %s", e)
    # endregion

    # region Updates sonar-scanner properties
    try:
        new_row = update_sonar_properties(version=version, dry_run=dry_run)
        logger.debug("bump_release() `sonar`: new_row = %s", new_row)
    except helpers.NothingToDoException as e:
        logger.info("No release section for `sonar`: %s", e)
    # endregion

    # region Updates sphinx file
    try:
        new_row = update_docs_conf(version=version, dry_run=dry_run)
        logger.debug("bump_release() `docs`: new_row = %s", new_row)
    except helpers.NothingToDoException as e:
        logger.info("No release section for `docs`: %s", e)
    # endregion

    # region Updates node packages file
    try:
        new_row = update_node_package(version=version, dry_run=dry_run)
        logger.debug("bump_release() `docs`: new_row = %s", new_row)
    except helpers.NothingToDoException as e:
        logger.info("No release section for `node`: %s", e)
    # endregion

    # region Updates YAML file
    try:
        new_row = update_ansible_vars(version=version, dry_run=dry_run)
        logger.debug("bump_release() `docs`: new_row = %s", new_row)
    except helpers.NothingToDoException as e:
        logger.info("No release section for `node`: %s", e)
    # endregion

    # region Updates the release.ini file with the new release number
    new_content = update_release_ini(path=release_file, version=version, dry_run=dry_run)
    logger.debug("bump_release() `release.ini`: new_row = %s", new_content)
    # endregion

    return 0


def update_main_file(version: Tuple[str, str, str], dry_run: bool = True
) -> str:
    """
    Updates the main django settings file, or a python script with

    :param version: Release number tuple (major, minor, release)
    :param dry_run: If `True`, no operation performed
    :return: changed string
    """
    try:
        path = RELEASE_CONFIG.get("main_project", "path")
        pattern = RELEASE_CONFIG.get("main_project", "pattern", fallback=helpers.MAIN_PROJECT_PATTERN)
        template = RELEASE_CONFIG.get("main_project", "template", fallback=helpers.MAIN_PROJECT_TEMPLATE)
    except configparser.Error as e:
        raise helpers.NothingToDoException(e)
    return helpers.update_file(path=path, pattern=pattern, template=template, release_number=version,
                               dry_run=dry_run)


def update_sonar_properties(version: Tuple[str, str, str], dry_run: Optional[bool] = False) -> str:
    """
    Updates the sonar-project.properties file with the new release number

    :param version: Release number tuple (major, minor, release)
    :param dry_run: If `True`, no operation performed
    :return: changed string
    """
    try:
        path = RELEASE_CONFIG.get("sonar", "path")
        pattern = RELEASE_CONFIG.get("sonar", "pattern", fallback=helpers.SONAR_PATTERN)
        template = RELEASE_CONFIG.get("sonar", "template", fallback=helpers.SONAR_TEMPLATE)
    except configparser.Error as e:
        raise helpers.NothingToDoException(e)
    return helpers.update_file(path=path, pattern=pattern, template=template, release_number=version,
                               dry_run=dry_run)


def update_docs_conf(version: Tuple[str, str, str], dry_run: Optional[bool] = False) -> str:
    """
    Updates the Sphinx conf.py file with the new release number

    :param version: Release number tuple (major, minor, release)
    :param dry_run: If `True`, no operation performed
    :return: changed string
    """
    try:
        path = RELEASE_CONFIG.get("docs", "path")
        pattern_release = RELEASE_CONFIG.get("docs", "pattern_release", fallback=helpers.DOCS_RELEASE_PATTERN)
        template_release = RELEASE_CONFIG.get("docs", "template_release", fallback=helpers.DOCS_RELEASE_FORMAT)

        pattern_version = RELEASE_CONFIG.get("docs", "pattern_version", fallback=helpers.DOCS_VERSION_PATTERN)
        template_version = RELEASE_CONFIG.get("docs", "re", fallback=helpers.DOCS_VERSION_FORMAT)
    except configparser.Error as e:
        raise helpers.NothingToDoException(e)

    update_release = helpers.update_file(path=path, pattern=pattern_release, template=template_release,
                                         release_number=version,
                                         dry_run=dry_run)
    update_version = helpers.update_file(path=path, pattern=pattern_version, template=template_version,
                                         release_number=version,
                                         dry_run=dry_run)
    return update_release + update_version


def update_node_package(version: Tuple[str, str, str], dry_run: Optional[bool] = False) -> str:
    """
    Updates the nodejs package file with the new release number

    :param version: Release number tuple (major, minor, release)
    :param dry_run: If `True`, no operation performed
    :return: changed string
    """
    try:
        path = RELEASE_CONFIG.get("node", "path")
        key = RELEASE_CONFIG.get("node", "key", fallback=helpers.NODE_KEY)
    except configparser.Error as e:
        raise helpers.NothingToDoException(e)
    return helpers.update_node_packages(path=path, version=version, key=key, dry_run=dry_run)


def update_ansible_vars(version: Tuple[str, str, str], dry_run: Optional[bool] = False) -> str:
    """
    Updates the ansible project variables file with the new release number

    :param version: Release number tuple (major, minor, release)
    :param dry_run: If `True`, no operation performed
    :return: changed string
    """
    try:
        path = RELEASE_CONFIG.get("ansible", "path")
        key = RELEASE_CONFIG.get("ansible", "key", fallback=helpers.ANSIBLE_KEY)
    except configparser.Error as e:
        raise helpers.NothingToDoException(e)
    return helpers.updates_yml_file(path=path, version=version, key=key, dry_run=dry_run)


def update_release_ini(path: str, version: Tuple[str, str, str], dry_run: Optional[bool] = False) -> str:
    """
    Updates the release.ini file with the new release number

    :param path: Release file path
    :param version: release number, as (<major>, <minor>, <release>)
    :param dry_run: If `True`, the operation WILL NOT be performed
    :return: Updated lines
    """
    config = configparser.ConfigParser()
    with open(path, "r+") as release_file:
        config.read(release_file)
        config.set("DEFAULT", "current_release", ".".join(version))
        if not dry_run:
            config.write(release_file)
        # Build text output
        stream = StringIO()
        config.write(stream)
        return stream.getvalue()
