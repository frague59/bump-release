# coding: utf-8
"""
Update release numbers in various places, according to a release.ini file places at the project root
+ [sonar]
  path = sonar-project.properties # Mandatory
  pattern = "^sonar.projectVersion=([.\\d]+)$"
  template = "sonar.projectVersion={major}.{minor}\n"
+ []
+ INI: release.ini
"""
import click
import configparser
import logging
from io import StringIO
from pathlib import Path
from typing import Tuple, Optional
from bump_release import helpers

logger = logging.getLogger("bump_release")

__version__ = VERSION = "0.3.0"

DEBUG = True

@click.command()
def update_files(
        version: Tuple[str, str, str],
        release_file: Optional[str] = None,
        dry_run: bool = True,
):
    """
    Updates the files according to the release.ini file

    :param version: Number
    :param release_file: path to the release.ini config file
    :param dry_run: If `True`, no operation performed
    :return: 0 if no error...
    """
    logging.info("Current config file: %s", release_file)

    # region Updates the main project (DJANGO_SETTINGS_MODULE file for django projects, __init__.py file...)
    try:
        new_row = update_main_file(version=version, dry_run=dry_run)
        logger.debug("update_files() `main_project`: new_row = %s", new_row)
    except helpers.NothingToDoException as e:
        logger.info("No release section for `main_project`: %s", e)
    # endregion

    # region Updates sonar-scanner properties
    try:
        new_row = update_sonar_properties(version=version, dry_run=dry_run)
        logger.debug("update_files() `sonar`: new_row = %s", new_row)
    except helpers.NothingToDoException as e:
        logger.info("No release section for `sonar`: %s", e)
    # endregion

    # region Updates sphinx file
    try:
        new_row = update_docs_conf(version=version, dry_run=dry_run)
        logger.debug("update_files() `docs`: new_row = %s", new_row)
    except helpers.NothingToDoException as e:
        logger.info("No release section for `docs`: %s", e)
    # endregion

    # region Updates node packages file
    try:
        new_row = update_node_package(version=version, dry_run=dry_run)
        logger.debug("update_files() `docs`: new_row = %s", new_row)
    except helpers.NothingToDoException as e:
        logger.info("No release section for `node`: %s", e)
    # endregion

    # region Updates YAML file
    try:
        new_row = update_ansible_vars(version=version, dry_run=dry_run)
        logger.debug("update_files() `docs`: new_row = %s", new_row)
    except helpers.NothingToDoException as e:
        logger.info("No release section for `node`: %s", e)
    # endregion

    # region Updates the release.ini file with the new release number
    ret = update_release_ini(path=release_file, version=version, dry_run=dry_run)
    if ret != 0:
        return ret
    # endregion

    return 0


def update_main_file(
        path: str, version: Tuple[str, str, str], dry_run: bool = True
) -> str:
    """
    Updates the main django settings file, or a python script with

    .. code-block:: python
       ...
       __version__ = VERSION = "<major>.<minor>.<release>"
       ...

    :param path: main file path
    :param version: Release number tuple (major, minor, release)
    :param dry_run: If `True`, no operation performed
    :return: Nothing
    """
    pattern = helpers.RELEASE_CONFIG.get("main_project", "pattern", fallback=helpers.MAIN_PROJECT_PATTERN)
    template = helpers.RELEASE_CONFIG.get("main_project", "template", fallback=helpers.MAIN_PROJECT_TEMPLATE)

    return helpers.update_file(path=path, pattern=pattern, template=template, release_number=version,
                               dry_run=dry_run)


def update_sonar_properties(path: str, version: Tuple[str, str, str], dry_run: Optional[bool] = False) -> str:
    """
    Updates the sonar-project.properties file with the new version number
    :param path:
    :param version:
    :param dry_run:
    :return:
    """
    try:
        pattern = helpers.RELEASE_CONFIG.get("sonar", "pattern", fallback=helpers.SONAR_PATTERN)
        template = helpers.RELEASE_CONFIG.get("sonar", "template", fallback=helpers.SONAR_TEMPLATE)
    except configparser.Error as e:
        raise helpers.NothingToDoException(e)
    return helpers.update_file(path=path, pattern=pattern, template=template, release_number=version,
                               dry_run=dry_run)


def update_docs_conf(path: str, version: Tuple[str, str, str], dry_run: Optional[bool] = False) -> str:
    """
    Updates the Sphinx conf.py file with the new version number

    :param path: File path
    :param version: version number, as (<major>, <minor>, <release>)
    :param dry_run: If `True`, the operation WILL NOT be performed
    :return: Updated lines
    """
    try:
        pattern_release = helpers.RELEASE_CONFIG.get("docs", "pattern_release", fallback=helpers.DOCS_RELEASE_PATTERN)
        template_release = helpers.RELEASE_CONFIG.get("docs", "template_release", fallback=helpers.DOCS_RELEASE_FORMAT)

        pattern_version = helpers.RELEASE_CONFIG.get("docs", "pattern_version", fallback=helpers.DOCS_VERSION_PATTERN)
        template_version = helpers.RELEASE_CONFIG.get("docs", "re", fallback=helpers.DOCS_VERSION_FORMAT)
    except configparser.Error as e:
        raise helpers.NothingToDoException(e)

    update_release = helpers.update_file(path=path, pattern=pattern_release, template=template_release,
                                         release_number=version,
                                         dry_run=dry_run)
    update_version = helpers.update_file(path=path, pattern=pattern_version, template=template_version,
                                         release_number=version,
                                         dry_run=dry_run)
    return update_release + update_version


def update_node_package(path: str, version: Tuple[str, str, str], dry_run: Optional[bool] = False) -> str:
    """
    Updates the nodejs package file with the new version number

    :param path: File path
    :param version: version number, as (<major>, <minor>, <release>)
    :param dry_run: If `True`, the operation WILL NOT be performed
    :return: Updated lines
    """

    try:
        key = helpers.RELEASE_CONFIG.get("node", "key", fallback=helpers.NODE_KEY)
    except configparser.Error as e:
        raise helpers.NothingToDoException(e)
    return helpers.update_node_packages(path=path, version=version, key=key, dry_run=dry_run)


def update_ansible_vars(path: str,  version: Tuple[str, str, str], dry_run: Optional[bool] = False) -> str:
    """
    Updates the ansible project variables file with the new version number

    :param path: File path
    :param version: version number, as (<major>, <minor>, <release>)
    :param dry_run: If `True`, the operation WILL NOT be performed
    :return: Updated lines
    """
    try:
        key = helpers.RELEASE_CONFIG.get("ansible", "key", fallback=helpers.ANSIBLE_KEY)
    except configparser.Error as e:
        raise helpers.NothingToDoException(e)
    return helpers.updates_yml_file(path=path, version=version, key=key, dry_run=dry_run)


def update_release_ini(path: str, version: Tuple[str, str, str], dry_run: Optional[bool] = False) -> str:
    """
    Updates the release.ini file with the new version number

    :param path: File path
    :param version: version number, as (<major>, <minor>, <release>)
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
