#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    Paroli
#
#    copyright 2008  Openmoko
#    Guillaume Chereau (charlie@openmoko.org)
#
#    This file is part of Paroli.
#
#    Paroli is free software: you can redistribute it and/or modify it
#    under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Paroli is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Paroli.  If not, see <http://www.gnu.org/licenses/>.

"""DBus launcher paroli main script

Main script to start paroli.
"""

import os
import sys
import dbus
import dbus.service
from optparse import OptionParser
import logging

# This is to make sure that we use the local tichy lib if run from the
# test directory
sys.path.insert(0, '../core/')

import tichy

logger = logging.getLogger('scripts.paroli')


def parse_options():
    """Parse the command line options

    :Returns: the OptionParser result object
    """
    parser = OptionParser()
    parser.add_option("", "--experimental",
                      action='store_true', dest="experimental",
                      help="Use experimental features",
                      default=False)
    parser.add_option("", "--session",
                      action='store_const', dest='bus',
                      help="Connect to the session bus",
                      const='session', default='system')
    parser.add_option("", "--launch", dest='launch',
                      help="launch an applet using DBus",
                      metavar="APPLICATION",
                      default=None)
    parser.add_option("", "--cfgfile", dest="cfg_file",
                      help="specigy the configuration file to use",
                      metavar="FILE", default=None)

    (options, args) = parser.parse_args()
    return options


def setup_logging():
    """Set up two logging handlers, one in the log file, one in the
    stdoutput"""
	# TODO: read a config file here
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s(%(filename)s:%(lineno)d) %(message)s',
        )


class InitAll(tichy.Tasklet):
    """Perform all basic initialization of services"""

    def run(self):
        yield tichy.Service.init_all()
        logger.info("start AutoAnswerCall")
        yield AutoAnswerCall()


class AutoAnswerCall(tichy.Tasklet):

    def run(self):
        # We don't create any window, just run in the background...
        # warning; that would only work with gtk or etk backend...
        gsm_service = tichy.Service.get('GSM')
        while True:
            call = yield tichy.Wait(gsm_service, 'incoming-call')
            logger.info("got incoming call")
            caller_service = tichy.Service.get('TeleCaller2')
            yield caller_service.call("None", call)


def set_default_services():
    """Set default services"""
    defaults = tichy.config.get('services', 'defaults', None)
    if not defaults:
        return {}
    defaults = defaults.split(',')

    for default in defaults:
        if not default:
            continue
        service, name = default.strip().split(':')
        tichy.Service.set_default(service, name)


class Launcher(dbus.service.Object):
    """Launch applets via DBus call

    example, to launch the Contacts application, using dbus-send :
      dbus-send --system --dest='org.tichy' /Launcher --print-reply \
      org.tichy.Launcher.Launch string:Contacts
    """

    def __init__(self, *args, **kargs):
        super(Launcher, self).__init__(*args, **kargs)
        self.screen = None
        logger.info("registered applications :")
        for app in tichy.Application.subclasses:
            if app.name:
                logger.info("- %s", app.name)

    @dbus.service.method("org.tichy.Launcher", "s")
    def Launch(self, name):
        """Launch a registered tichy application by name"""
        logger.info("launch %s", name)
        try:
            app = tichy.Application.find_by_name(name)
            self.launch(app).start()
        except KeyError:
            logger.error("no application named  %s", name)

    @tichy.tasklet.tasklet
    def launch(self, app):
        """Actually launch the application"""
        kill_on_close = False
        if not self.screen:
            self.screen = self.create_screen()
            kill_on_close = False
        try:
            yield app(None)
        except Exception, ex:
            logger.error("application %s failed : %s", app.name, ex)
            import traceback
            logger.error(traceback.format_exc())
        if kill_on_close:
            self.screen.destroy()
            self.screen = None

    def create_screen(self):
        window = None
        return window

    @dbus.service.method("org.tichy.Launcher")
    def Quit(self):
        """Quit paroli"""
        logger.info("quit mainloop")
        tichy.mainloop.quit()


def launch(name, options):
    """Use dbus to call the launcher"""
    if options.bus == 'system':
        bus = dbus.SystemBus()
    else:
        bus = dbus.SessionBus()
    launcher = bus.get_object('org.tichy.launcher', '/Launcher')
    launcher = dbus.Interface(launcher, 'org.tichy.Launcher')
    launcher.Launch(options.launch)


if __name__ == '__main__':
    options = parse_options()

    setup_logging()
    tichy.config.parse(cfg_file=options.cfg_file)
    
    if tichy.config.getboolean('dbus','activated', False):
        logger.info("connect to dbus")
        if options.bus == 'system':
            bus = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
        else:
            bus = dbus.SessionBus(mainloop=tichy.mainloop.dbus_loop)
        
        if bus.list_activatable_names().count('org.tichy.launcher') != 0:
            logger.info("paroli already running")
            if options.launch:
                logger.info("running launch")
                launch(options.launch, options)
                sys.exit(0)
        
        bus_name = dbus.service.BusName('org.tichy.launcher', bus)


        logger.info("start launcher service")
        launcher = Launcher(bus, '/Launcher')

    # We set the default service before importing the plugins
    set_default_services()

    # We import all the modules into the plugin directory
    default_plugins_path = '/usr/share/tichy/plugins'
    plugins_dir = tichy.config.get('plugins', 'path', default_plugins_path)
    plugins_dirs = plugins_dir.split(':')
    for plugins_dir in plugins_dirs:
        logger.debug('plugins_dir: %s', plugins_dir)
        try:
            logger.info("try to load plugins in %s", plugins_dir)
            tichy.plugins.import_all(plugins_dir)
        except IOError:
            logger.info("failed to load plugins in %s", plugins_dir)

    logger.info("start InitAll")
    InitAll().start()

    app_name = tichy.config.get('autolaunch', 'application', None)
    if app_name:
        standalone = tichy.config.getboolean('standalone', 'activated', False)
        for app in tichy.Application.subclasses:
            if app.name == app_name:
                app("None", standalone=standalone).start()


    logger.info("starting mainloop")
    tichy.mainloop.run()
    tichy.Service.end_all()
    
    logger.info("quit")
