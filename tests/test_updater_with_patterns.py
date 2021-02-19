"""
Tests for updaters
"""
import logging
import sys
from pathlib import Path

import pytest

import bump_release
from bump_release import helpers

logger = logging.getLogger("tests")

MODULE_PATH = Path(__file__).parent


@pytest.fixture
def config():
    release_ini_path = Path(__file__).parent / "fixtures" / "release_with_patterns.ini"
    config = helpers.load_release_file(release_ini_path)
    logger.info("config() Config file loaded")
    assert config
    return config


@pytest.fixture
def version():
    splited_version = helpers.split_version("0.1.0")
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
    assert config.has_section("setup"), "No `setup` section in release.ini file"
    assert config.has_section("ansible"), "No `ansible` section in release.ini file"


def test_main_project_params(config):
    assert config["main_project"].get("path")
    assert config["main_project"].get("pattern", "")
    assert config["main_project"].get("template", "")


def test_update_main_project(config, version):
    str_path = config["main_project"].get("path")
    assert str_path is not None
    path = Path(str_path)
    print(f"DEBUG::test_update_main_project() path = {path.absolute()}", file=sys.stderr)
    pattern = config["main_project"].get("pattern", "").strip('"')
    template = config["main_project"].get("template", "").strip('"')
    assert pattern != "", "No `pattern` key found for `main_project` section"
    assert template != "", "No `template` key found for `main_project` section"
    new_row = helpers.update_file(
        path=path,
        pattern=pattern or helpers.MAIN_PROJECT_PATTERN,
        template=template or helpers.MAIN_PROJECT_TEMPLATE,
        version=version,
        dry_run=True,
    )
    assert new_row is not None, "MAIN: No row returned"
    assert new_row.strip() == "__version__ = VERSION = '0.1.0'", "MAIN: Versions does not match"


def test_update_sonar_properties(config, version):
    str_path = config["sonar"].get("path")
    assert str_path is not None
    path = Path(str_path)
    print(f"DEBUG::test_update_sonar_properties() path = {path.absolute()}", file=sys.stderr)

    pattern = config["sonar"].get("pattern", "").strip('"')
    template = config["sonar"].get("template", "").strip('"')
    assert pattern != "", "No `pattern` key found for `sonar` section"
    assert template != "", "No `template` key found for `sonar` section"

    new_row = helpers.update_file(
        path=path,
        pattern=pattern or helpers.SONAR_PATTERN,
        template=template or helpers.SONAR_TEMPLATE,
        version=version,
        dry_run=True,
    )
    assert new_row is not None, "SONAR: No row returned"
    assert new_row.strip() == "sonar.projectVersion=0.1", "SONAR: Versions does not match"


def test_update_docs(config, version):
    str_path = config["docs"].get("path")
    assert str_path is not None
    path = Path(str_path)
    print(f"DEBUG::test_update_docs() path = {path.absolute()}", file=sys.stderr)

    version_pattern = config["docs"].get("version_pattern") or helpers.DOCS_VERSION_PATTERN
    version_pattern = version_pattern.strip('"')
    version_format = config["docs"].get("version_format") or helpers.DOCS_VERSION_FORMAT
    version_format = version_format.strip('"')

    release_pattern = config["docs"].get("release_pattern") or helpers.DOCS_RELEASE_PATTERN
    release_pattern = release_pattern.strip('"')
    release_format = config["docs"].get("release_format") or helpers.DOCS_RELEASE_FORMAT
    release_format = release_format.strip('"')

    assert version_pattern != "", "No `version_pattern` key found for `docs` section"
    assert version_format != "", "No `version_format` key found for `docs` section"

    assert release_pattern != "", "No `release_pattern` key found for `docs` section"
    assert release_format != "", "No `release_format` key found for `docs` section"

    new_row = helpers.update_file(
        path=path,
        pattern=release_pattern,
        template=release_format,
        version=version,
        dry_run=True,
    )
    assert new_row.strip() == "release = '0.1.0'", "DOCS: Versions does not match"

    new_row = helpers.update_file(
        path=path,
        pattern=version_pattern,
        template=version_format,
        version=version,
        dry_run=True,
    )
    assert new_row.strip() == "version = '0.1'", "DOCS: Versions does not match"


def test_update_node_packages(config, version):
    str_path = config.get(
        "node",
        "path",
        fallback=str(Path(__file__).parent / "fixtures" / "assets" / "package.json"),
    )
    assert str_path is not None
    path = Path(str_path)
    print(f"DEBUG::test_update_node_packages() path = {path.absolute()}", file=sys.stderr)

    key = config.get("node", "key", fallback=helpers.NODE_KEY)
    new_content = helpers.update_node_packages(path=path, version=version, key=key)
    assert new_content, "NODE: New content cannot be empty"


def test_update_ansible(config, version):
    str_path = config.get("ansible", "path", fallback="vars.yml")
    key = config.get("ansible", "key", fallback="git.release")
    assert str_path is not None
    path = Path(str_path)
    print(f"DEBUG::test_update_ansible() path = {path.absolute()}", file=sys.stderr)

    new_content = helpers.updates_yaml_file(path=path, version=version, key=key)
    assert new_content, "ANSIBLE: New content cannot be empty"


def test_full_update_ansible(config, version):
    bump_release.RELEASE_CONFIG = config
    result = bump_release.update_ansible_vars(version=version, dry_run=True)
    assert result is not None


def test_full_docs_conf(config, version):
    bump_release.RELEASE_CONFIG = config
    result = bump_release.update_docs_conf(version=version, dry_run=True)
    assert result is not None


def test_full_main_project(config, version):
    bump_release.RELEASE_CONFIG = config
    result = bump_release.update_main_file(version=version, dry_run=True)
    assert result is not None


def test_full_node_package(config, version):
    bump_release.RELEASE_CONFIG = config
    result = bump_release.update_node_package(version=version, dry_run=True)
    assert result is not None


def test_full_sonar_properties(config, version):
    bump_release.RELEASE_CONFIG = config
    result = bump_release.update_node_package(version=version, dry_run=True)
    assert result is not None
