# -*- coding: utf-8 -*-
"""
__main__ for :mod:`bump_release` application

:creationdate: 17/09/2019 11:52
:moduleauthor: François GUÉRIN <fguerin@ville-tourcoing.fr>
:modulename: bump_release.__main__

"""
import sys
import logging
from bump_release import bump_release

__author__ = 'fguerin'
logger = logging.getLogger('bump_release.__main__')

bump_release()
