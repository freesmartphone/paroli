#    Tichy
#    copyright 2008 Guillaume Chereau (charlie@openmoko.org)
#
#    This file is part of Tichy.
#
#    Tichy is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Tichy is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Tichy.  If not, see <http://www.gnu.org/licenses/>.


import os
import os.path
import sys

import logging
logger = logging.getLogger('plugins')


def get_all_module_paths(dir):
    for root, dirs, files in os.walk(dir):
        if '%s.py' % os.path.basename(root) in files:
            yield root
            dirs[:] = []


def import_all(dir):
    logger.info("import_all %s", dir)
    if not os.path.exists(dir):
        logger.info("path '%s' does not exist", dir)
        raise IOError
    for path in get_all_module_paths(dir):
        import_single(path)


def import_single(dir):
    name = os.path.basename(dir)
    sys_path = sys.path[:]
    sys.path.insert(0, dir)
    try:
        __import__(name)
        logger.info("import %s", dir)
    except ImportError, e:
        logger.error("can't import %s : %s", dir, e)
        raise
    finally:
        sys.path[:] = sys_path


if __name__ == '__main__':
    for p in get_all_module_paths("."):
        print p
