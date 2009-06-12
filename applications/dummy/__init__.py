# -*- coding: utf-8 -*-

from logging import getLogger
logger = getLogger('applications.dummy')

from os.path import join as pjoin, dirname
from tichy import Application
from tichy.tasklet import Sleep
from gui import elm_layout_window

class Dummy(Application):
	name = 'Dummy'
	icon = 'icon.png'
	category = 'launcher' # So that we see the app in the launcher

	def run(self, parent=None, standalone=False):
		logger.info('run starts')
		edje_file = pjoin(dirname(__file__), 'dummy.edj')
		window = elm_layout_window(edje_file, "dummy", None, None, True)
		window.main_layout.elm_obj.edje_get().part_text_set('dummy.textview', '''
<h1>I`m a dummy</h1>
<p><strong>Hihi bla fasel</strong></p>
<p><red>Hihi bla fasel</red></p>
''')
		yield Sleep(5)
		window.delete()
		logger.info('run stops')
# vim:tw=0:nowrap