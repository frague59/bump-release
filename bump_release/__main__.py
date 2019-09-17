# -*- coding: utf-8 -*-
"""
__main__ for :mod:`bump_release` application

:creationdate: 17/09/2019 11:52
:moduleauthor: François GUÉRIN <fguerin@ville-tourcoing.fr>
:modulename: bump_release.__main__

"""
import os
import sys
import logging
from pathlib import Path

import bump_release
from bump_release import helpers

__author__ = 'fguerin'
logging = logging.getLogger('bump_release')

if __name__ == "__main__":
    bump_release.RELEASE_FILE = Path(os.getcwd()) / "release.ini"
    bump_release.RELEASE_CONFIG = helpers.load_release_file(release_file=bump_release.RELEASE_FILE)
    result = bump_release.process_update(release="0.4.3", dry_run=True, debug=True)
    sys.exit(result)

