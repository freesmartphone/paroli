#!/usr/bin/env python

#    Paroli
#
#    copyright 2008 OpenMoko
#
#    This file is part of Paroli.
#
#    Paroli is free software: you can redistribute it and/or modify it
#    under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Tichy is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Paroli.  If not, see <http://www.gnu.org/licenses/>.

# XXX: This file only work when used by OpenEmbedded.  We should fix
#      that !

import sys
import os

from distutils.core import setup
from distutils.extension import Extension
from glob import glob
import commands

from distutils.command.build import build as _build
from distutils.command.clean import clean as _clean

class my_build(_build):
    def run(self):
        _build.run(self)

        # compile theme files
        import subprocess
        result = subprocess.call("cd ./paroli-applications; ./build.sh", shell=True)
        if result != 0:
            raise Exception("Can't build theme files. Built edje_cc?")

class my_clean(_clean):
    def run(self):
        _clean.run(self)
        # XXX: add cleaning of the .edj files


def plugins_files(source, dest):
    """generate the plugins data files list

    It works by adding all the files ending with a set of specified
    extension to the data. So we have to be careful when adding files
    with new extension we have to add it here as well.
    """
    ret = []
    for root, dirs, files in os.walk(source):
        # XXX: Where is the best place to put the plugins files ???
        # XXX: this [len(source)+1:] is messy,
        # clean that.
        f_dest = os.path.join(dest, root[len(source)+1:])
        src = []
        for file in files:
            if file.endswith((".py", ".ttf", ".png", ".dic", ".txt",
                              ".edj", ".edc")):
                path = '%s/%s' % (root, file)
                src.append(path)
        ret.append((f_dest, src))
    return ret

dbus_data = [
    (os.path.join(sys.prefix, 'share/dbus-1/system-services/'),
     ['data/dbus/org.tichy.launcher.service']),
    ('../../etc/dbus-1/system.d/',
     ['data/dbus/tichy.conf'])]

setup(name='Paroli',
      version='0.1',
      description="Paroli",
      author="Mirko Lindler",
      author_email='mirko@openmoko.org',
      package_dir = {'': 'paroli-core'},
      packages = ['tichy', 'tichy.gui_paroli'],
      scripts= ['paroli-scripts/paroli-launcher'],
      # XXX: Those locations may not work on the neo !
      data_files = [('applications',
                     ['data/paroli-launcher.desktop',
                      'data/paroli-io.desktop',
                      'data/paroli-contacts.desktop',
                      'data/paroli-msgs.desktop',
                      'data/paroli-dialer.desktop']),
                    (os.path.join(sys.prefix, 'share/pixmaps/'),
                     ['data/tichy']),
                    ('../../etc/paroli/', ['data/paroli.cfg'])] \
          + plugins_files('paroli-services', 'share/paroli/services') \
          + plugins_files('paroli-applications', 'share/paroli/applications') \
          + dbus_data,

      cmdclass = {'build': my_build,
                  'clean': my_clean},
      
      )


