# -*- coding: utf-8 -*-
"""
__main__ for :mod:`bump_release` application

:creationdate: 17/09/2019 11:52
:moduleauthor: François GUÉRIN <fguerin@ville-tourcoing.fr>
:modulename: bump_release.__main__

"""
import sys
from pathlib import Path

import bump_release
from bump_release import helpers

__author__ = "fguerin"

if __name__ == "__main__":
    bump_release.RELEASE_FILE = Path.cwd() / "release.ini"
    bump_release.RELEASE_CONFIG = helpers.load_release_file(
        release_file=bump_release.RELEASE_FILE
    )
    result = bump_release.process_update(
        release_file=bump_release.RELEASE_FILE,
        release="0.4.4",
        dry_run=True,
        debug=False,
    )
    sys.exit(result)
