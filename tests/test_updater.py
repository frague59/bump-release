# -+- coding: utf-8 -+-
"""
Tests for updaters
"""
import logging
import pytest
from pathlib import Path
from typing import Union
from bump_release import helpers

logger = logging.getLogger("tests")

MODULE_PATH = Path(__file__).parent


@pytest.fixture
def config():
    config = helpers.load_release_file(MODULE_PATH / "fixtures" / "release.ini")
    logger.info("config() Config file loaded")
    assert config
    return config


@pytest.fixture
def version():
    splited_version = helpers.split_version("1.1.1")
    return splited_version


def test_load_release_file(config):
    """
    Tests the loading and the values of the release.ini file

    :param config:
    :return:
    """
    assert config.has_section("main_project"), "No `main_project` section in release.ini file"
    assert config.has_section("sonar"), "No `sonar` section in release.ini file"
    assert config.has_section("docs"), "No `docs` section in release.ini file"
    assert config.has_section("ansible"), "No `ansible` section in release.ini file"

    assert config.has_option("DEFAULT", "current_release"), "No `DEFAULT.current_release` value in release.ini file"
    assert config.has_option("main_project", "path"), "No `main_project.path` value in release.ini file"
    assert config.has_option("sonar", "path"), "No `sonar.path` value in release.ini file"
    assert config.has_option("docs", "path"), "No `docs.path` value in release.ini file"
    assert config.has_option("ansible", "path"), "No `ansible.path` value in release.ini file"


def test_version():
    splited_version = helpers.split_version("0.0.1")
    assert splited_version == ("0", "0", "1"), "Version for `0.0.1` MUST BE ('0', '0', '1')"
    splited_version = helpers.split_version("1.1.1")
    assert splited_version == ("1", "1", "1"), "Version for `1.1.1` MUST BE ('1', '1', '1')"
    splited_version = helpers.split_version("1.1.1a")
    assert splited_version == ("1", "1", "1a"), "Version for `1.1.1a` MUST BE ('1', '1', '1a')"
    splited_version = helpers.split_version("1.1.1b")
    assert splited_version == ("1", "1", "1b"), "Version for `1.1.1b` MUST BE ('1', '1', '1b')"


def test_update_main_project(config, version):
    str_path = config["main_project"].get("path")
    assert str_path is not None
    path = MODULE_PATH / str_path
    new_row = helpers.update_file(path=path, pattern=helpers.MAIN_PROJECT_PATTERN, template=helpers.MAIN_PROJECT_TEMPLATE,
                                  release_number=version, dry_run=True)
    assert new_row.strip() == "__version__ = VERSION = \"1.1.1\"", "MAIN: Versions does not match"


def test_update_sonar_properties(config, version):
    str_path = config["sonar"].get("path")
    assert str_path is not None
    path = MODULE_PATH / str_path
    new_row = helpers.update_file(path=path, pattern=helpers.SONAR_PATTERN, template=helpers.SONAR_TEMPLATE,
                                  release_number=version, dry_run=True)
    assert new_row.strip() == "sonar.projectVersion=1.1", "SONAR: Versions does not match"


def test_update_docs(config, version):
    str_path = config.get("docs", "path")
    assert str_path is not None
    path = MODULE_PATH / str_path
    version_pattern = config.get("docs", "version_pattern", fallback=helpers.DOCS_VERSION_PATTERN)
    release_pattern = config.get("docs", "release_pattern", fallback=helpers.DOCS_RELEASE_PATTERN)
    version_format = config.get("docs", "version_format", fallback=helpers.DOCS_VERSION_FORMAT)
    release_format = config.get("docs", "release_format", fallback=helpers.DOCS_RELEASE_FORMAT)
    new_row = helpers.update_file(path=path, pattern=release_pattern, template=release_format,
                                  release_number=version, dry_run=True)
    assert new_row.strip() == "release = \"1.1.1\"", "DOCS: Versions does not match"

    new_row = helpers.update_file(path=path, pattern=version_pattern, template=version_format,
                                  release_number=version, dry_run=True)
    assert new_row.strip() == "version = \"1.1\"", "DOCS: Versions does not match"


def test_update_node_packages(config, version):
    str_path = config.get("node", "path", fallback=str(Path(__file__).parent / "fixtures" / "assets" / "package.json"))
    assert str_path is not None
    path = MODULE_PATH / str_path
    key = config.get("node", "key", fallback=helpers.NODE_KEY)
    new_content = helpers.update_node_packages(path=path, version=version, key=key)
    assert new_content, "NODE: New content cannot be empty"


def test_update_ansible(config, version):
    str_path = config.get("ansible", "path", fallback="vars.yml")
    key = config.get("ansible", "key", fallback="git.version")
    assert str_path is not None
    path = MODULE_PATH / str_path
    new_content = helpers.updates_yml_file(path=path, version=version, key=key)
    assert new_content, "ANSIBLE: New content cannot be empty"
