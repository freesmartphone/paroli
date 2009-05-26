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


def _get_all_modules(path):
    for dir in os.listdir(path):
        if os.path.exists(os.path.join(path, dir, '__init__.py')): # TODO: check if there is a py std way for this
            yield dir
        else:
            logger.debug('ignored directory "%s"', dir)


def import_all(dir):
    logger.debug("import_all %s", dir)
    if not os.path.exists(dir):
        logger.error("path '%s' does not exist", dir)
        raise IOError
    sys_path = sys.path[:]
    sys.path.insert(0, dir)
    try:
        for module in _get_all_modules(dir):
            logger.debug("import_all %s %s", dir, module)
            __import__(module)
            logger.info("import %s", module)
    except ImportError, e:
        logger.exception("can't import %s : %s", dir, e)
        raise
    finally:
        sys.path[:] = sys_path


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(filename)s:%(lineno)d %(levelname)s %(name)s: %(message)s',
        )
    import_all(".")
