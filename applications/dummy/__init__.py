# -*- coding: utf-8 -*-

from os.path import join as pjoin, dirname
from logging import getLogger
logger = getLogger('applications.dummy')
from tichy import Application
from tichy.tasklet import Sleep
from gui import elm_layout, elm_window

class Dummy(Application):
	name = 'Dummy'
	icon = 'icon.png'
	category = 'launcher' # So that we see the app in the launcher

	def run(self, parent=None, standalone=False):
		logger.info('run starts')
		self.window = elm_window(self.name)
		self.edje_file = pjoin(dirname(__file__), 'dummy.edj')
		self.layout = elm_layout(self.window, self.edje_file, "dummy")
		self.window.elm_obj.resize_object_add(self.layout.elm_obj)
		self.window.elm_obj.show()
		self.layout.elm_obj.edje_get().part_text_set('dummy.textview', '''
<h1>I`m a dummy</h1>
<p><red>Hihi bla fasel</red></p>
''')
		yield Sleep(5)
		self.layout.elm_obj.delete()
		self.window.elm_obj.delete()
		logger.info('run stops')
# vim:tw=0:nowrap
