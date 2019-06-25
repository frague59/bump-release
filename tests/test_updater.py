"""
Tests for updaters
"""
from copy import deepcopy
from pathlib import Path
import configparser
from typing import Union

import pytest

import bump_release

MODULE_PATH = Path(__file__).parent

_CONFIG = configparser.ConfigParser()
_CONFIG.read("./fixtures/settings.ini")
bump_release.CONFIG = _CONFIG


def _find_row(
        file_name: str,
        row_strings: Union[str, tuple, list]
) -> bool:
    with open(file_name, "r") as text_file:
        lines = text_file.readlines()

    if isinstance(row_strings, str):
        row_strings = [row_strings, ]

    if isinstance(row_strings, tuple):
        row_strings = list(row_strings)
    found = []
    for line in lines:
        for row_string in row_strings:
            if line == row_string:
                found.append(row_string)
                break

    return len(row_strings) == len(found)


@pytest.fixture
def release():
    return bump_release.split_release("1.1.1")


@pytest.fixture
def main_module_text_file():
    path = _CONFIG.get("main_project", "path")
    new_path = MODULE_PATH / path
    print("main_module_text_file() new_path =", new_path)
    return str(new_path)


@pytest.fixture
def sonar_file():
    path = _CONFIG.get("sonar", "path")
    new_path = MODULE_PATH / path
    print("sonar_file() new_path =", new_path)
    return str(new_path)


@pytest.fixture
def sphinx_file():
    path = _CONFIG.get("docs", "path")
    new_path = MODULE_PATH / path
    print("docs_file() new_path =", new_path)
    return str(new_path)


def test_split_release():
    splited = bump_release.split_release("1.1.1")
    assert splited == ("1", "1", "1")

    splited = bump_release.split_release("1.1.1a")
    assert splited == ("1", "1", "1a")


def test_update_main_file(main_module_text_file, release):
    bump_release.update_main_file(
        path=main_module_text_file,
        release_number=release,
        dry_run=False
    )

    found = _find_row(main_module_text_file, "__version__ = VERSION = \"1.1.1\"\n")
    assert found


def test_update_sonar(sonar_file, release):
    bump_release.update_sonar_properties(
        path=sonar_file,
        release_number=release,
        dry_run=False
    )

    found = _find_row(sonar_file, "sonar.projectVersion=1.1\n")
    assert found


def test_update_sphinx(sphinx_file, release):
    bump_release.update_sphinx_conf(
        path=sphinx_file,
        release_number=release,
        dry_run=False
    )

    found = _find_row(sphinx_file, ("version = \"1.1\"\n", "release = \"1.1.1\"\n", ))
    assert found
